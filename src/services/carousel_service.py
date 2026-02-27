from __future__ import annotations

import asyncio
import json
import logging
import time

import httpx

from src.ai.anthropic_provider import AnthropicCopywriter
from src.ai.gemini_provider import GeminiImageProvider
from src.config.constants import (
    AVAILABLE_STYLES,
    CREDITS_PER_CAROUSEL,
    IMAGE_GEN_MAX_RETRIES,
    IMAGE_GEN_RETRY_BACKOFF,
    MAX_INPUT_TEXT_LENGTH,
    MAX_SLIDES_PER_CAROUSEL,
    MIN_SLIDES_PER_CAROUSEL,
    S3_CAROUSEL_PREFIX,
)
from src.config.settings import get_settings
from src.db.session import get_session_factory
from src.models.carousel import CarouselGeneration, GenerationStatus
from src.models.slide import Slide
from src.renderer.engine import SlideRenderer, load_cta_image
from src.renderer.styles import StyleConfig, load_style_config
from src.schemas.slide import SlideContent, SlideType
from src.services.credit_service import refund_credits
from src.storage.s3 import S3Client

logger = logging.getLogger(__name__)


class _ProgressCounter:
    """Thread-safe-style counter for tracking completed slides in async gather."""

    __slots__ = ("completed",)

    def __init__(self) -> None:
        self.completed: int = 0

    def increment(self) -> int:
        self.completed += 1
        return self.completed


class TelegramNotifier:
    """Edits a Telegram status message with progress updates."""

    def __init__(self, bot_token: str, chat_id: int, message_id: int) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._message_id = message_id
        self._last_text: str = ""
        self._client = httpx.AsyncClient(timeout=10)

    async def update(self, text: str) -> None:
        if text == self._last_text:
            return
        self._last_text = text
        try:
            await self._client.post(
                f"https://api.telegram.org/bot{self._bot_token}/editMessageText",
                json={
                    "chat_id": self._chat_id,
                    "message_id": self._message_id,
                    "text": text,
                },
            )
        except Exception:
            logger.debug("Failed to update status message", exc_info=True)

    async def close(self) -> None:
        await self._client.aclose()


class CarouselService:
    def __init__(self) -> None:
        self.copywriter = AnthropicCopywriter()
        self.image_provider = GeminiImageProvider()
        self.s3 = S3Client()

    async def _generate_slide_image_with_retry(
        self,
        slide: SlideContent,
        style_config: StyleConfig,
        semaphore: asyncio.Semaphore,
        notifier: TelegramNotifier,
        total: int,
        progress: _ProgressCounter,
    ) -> bytes | None:
        """Generate a single slide image with retries and concurrency limiting."""
        async with semaphore:
            for attempt in range(IMAGE_GEN_MAX_RETRIES + 1):
                result = await self.image_provider.generate_slide_image(
                    slide=slide,
                    style_config=style_config,
                )
                if result is not None:
                    count = progress.increment()
                    await notifier.update(
                        f"Generating slide images... ({count}/{total} ready)"
                    )
                    return result

                if attempt < IMAGE_GEN_MAX_RETRIES:
                    logger.warning(
                        "Slide %d image gen failed (attempt %d/%d), retrying...",
                        slide.position,
                        attempt + 1,
                        IMAGE_GEN_MAX_RETRIES + 1,
                    )
                    await asyncio.sleep(IMAGE_GEN_RETRY_BACKOFF * (attempt + 1))

            logger.warning("All retries exhausted for slide %d image generation", slide.position)
            count = progress.increment()
            await notifier.update(
                f"Generating slide images... ({count}/{total} ready)"
            )
            return None

    async def generate_and_send(
        self,
        user_id: int,
        telegram_chat_id: int,
        input_text: str,
        style_slug: str,
        status_message_id: int,
        celery_task_id: str | None = None,
    ) -> None:
        if len(input_text) > MAX_INPUT_TEXT_LENGTH:
            raise ValueError(f"Input text exceeds maximum length of {MAX_INPUT_TEXT_LENGTH}")
        if style_slug not in AVAILABLE_STYLES:
            raise ValueError(f"Unknown style slug: {style_slug}")

        settings = get_settings()
        bot_token = settings.telegram.bot_token.get_secret_value()
        max_concurrency = settings.gemini.max_concurrency
        factory = get_session_factory()

        notifier = TelegramNotifier(bot_token, telegram_chat_id, status_message_id)

        try:
            async with factory() as session:
                generation = CarouselGeneration(
                    user_id=user_id,
                    input_text=input_text,
                    style_slug=style_slug,
                    status=GenerationStatus.PENDING,
                    celery_task_id=celery_task_id,
                )
                session.add(generation)
                await session.commit()

                try:
                    # Step 1: AI Copywriting
                    generation.status = GenerationStatus.COPYWRITING
                    await session.commit()
                    await notifier.update("Writing carousel copy...")

                    slide_count = min(
                        max(MIN_SLIDES_PER_CAROUSEL, len(input_text) // 500 + 3),
                        MAX_SLIDES_PER_CAROUSEL,
                    )
                    slides_content = await self.copywriter.generate_slides(
                        input_text=input_text,
                        style_slug=style_slug,
                        slide_count=slide_count,
                    )
                    slides_content = slides_content[:MAX_SLIDES_PER_CAROUSEL]
                    generation.slide_count = len(slides_content)

                    # Step 2: Image generation — only for hook slide (slide 1)
                    generation.status = GenerationStatus.IMAGE_GENERATION
                    await session.commit()
                    await notifier.update("Generating hook slide image...")

                    style_config = load_style_config(style_slug)
                    semaphore = asyncio.Semaphore(max_concurrency)
                    progress = _ProgressCounter()

                    hook_slide = slides_content[0]
                    hook_image = await self._generate_slide_image_with_retry(
                        slide=hook_slide,
                        style_config=style_config,
                        semaphore=semaphore,
                        notifier=notifier,
                        total=1,
                        progress=progress,
                    )

                    # Load pre-made CTA image for this style
                    cta_image_bytes = load_cta_image(style_slug)

                    # Step 3: Rendering
                    generation.status = GenerationStatus.RENDERING
                    await session.commit()
                    await notifier.update(
                        f"Rendering {len(slides_content)} slides..."
                    )

                    renderer = SlideRenderer(style_config)
                    rendered_slides: list[bytes] = []

                    for sc in slides_content:
                        if sc.slide_type == SlideType.HOOK:
                            png_bytes = renderer.render(
                                slide=sc, generated_image=hook_image,
                            )
                        elif sc.slide_type == SlideType.CTA:
                            png_bytes = renderer.render(
                                slide=sc, cta_image=cta_image_bytes,
                            )
                        else:
                            png_bytes = renderer.render(slide=sc)
                        rendered_slides.append(png_bytes)

                    # Step 4: Upload to S3
                    generation.status = GenerationStatus.UPLOADING
                    await session.commit()

                    ts = int(time.time())
                    for i, (sc, png_bytes) in enumerate(
                        zip(slides_content, rendered_slides, strict=True)
                    ):
                        gen_id = generation.id
                        s3_key = f"{S3_CAROUSEL_PREFIX}/{user_id}/{gen_id}/{ts}_slide_{i}.png"
                        self.s3.upload_bytes(s3_key, png_bytes)

                        # Serialize template-specific data as JSON
                        template_data_json = None
                        if sc.listing_data:
                            template_data_json = sc.listing_data.model_dump_json()
                        elif sc.comparison_data:
                            template_data_json = sc.comparison_data.model_dump_json()

                        slide = Slide(
                            carousel_id=generation.id,
                            position=sc.position,
                            heading=sc.heading,
                            subtitle=sc.subtitle,
                            body_text=sc.body_text,
                            text_position=sc.text_position.value,
                            slide_type=sc.slide_type.value,
                            content_template=sc.content_template.value,
                            template_data=template_data_json,
                            rendered_s3_key=s3_key,
                        )
                        session.add(slide)

                    await session.commit()

                    # Step 5: Send to Telegram
                    generation.status = GenerationStatus.SENDING
                    await session.commit()
                    await notifier.update("Sending carousel...")

                    async with httpx.AsyncClient() as http:
                        media = []
                        files = {}
                        for i, png_bytes in enumerate(rendered_slides):
                            attach_name = f"slide_{i}"
                            media.append(
                                {
                                    "type": "photo",
                                    "media": f"attach://{attach_name}",
                                }
                            )
                            files[attach_name] = (f"{attach_name}.png", png_bytes, "image/png")

                        resp = await http.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMediaGroup",
                            data={
                                "chat_id": telegram_chat_id,
                                "media": json.dumps(media),
                            },
                            files=files,
                            timeout=60,
                        )
                        resp_data = resp.json()
                        if resp.status_code != 200 or not resp_data.get("ok"):
                            desc = resp_data.get("description", "")
                            raise RuntimeError(f"sendMediaGroup failed: {resp.status_code} {desc}")

                        # Delete status message
                        await http.post(
                            f"https://api.telegram.org/bot{bot_token}/deleteMessage",
                            json={
                                "chat_id": telegram_chat_id,
                                "message_id": status_message_id,
                            },
                            timeout=10,
                        )

                    generation.status = GenerationStatus.COMPLETED
                    await session.commit()
                    logger.info("Carousel %d completed for user %d", generation.id, user_id)

                except Exception as e:
                    generation.status = GenerationStatus.FAILED
                    generation.error_message = str(e)[:500]
                    await session.commit()

                    try:
                        await refund_credits(
                            session=session,
                            user_id=user_id,
                            amount=CREDITS_PER_CAROUSEL,
                            generation_id=generation.id,
                        )
                        await session.commit()
                    except Exception:
                        logger.exception("Failed to refund credits for user %d", user_id)

                    async with httpx.AsyncClient() as http:
                        await http.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json={
                                "chat_id": telegram_chat_id,
                                "text": (
                                    "Sorry, carousel generation failed. "
                                    "Your credits have been refunded."
                                ),
                            },
                            timeout=10,
                        )

                    raise
        finally:
            await notifier.close()

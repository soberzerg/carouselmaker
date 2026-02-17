from __future__ import annotations

import json
import logging
import time

import httpx

from src.ai.anthropic_provider import AnthropicCopywriter
from src.ai.gemini_provider import GeminiImageProvider
from src.config.constants import (
    AVAILABLE_STYLES,
    CREDITS_PER_CAROUSEL,
    MAX_INPUT_TEXT_LENGTH,
    MAX_SLIDES_PER_CAROUSEL,
    MIN_SLIDES_PER_CAROUSEL,
    S3_CAROUSEL_PREFIX,
)
from src.config.settings import get_settings
from src.db.session import get_session_factory
from src.models.carousel import CarouselGeneration, GenerationStatus
from src.models.slide import Slide
from src.renderer.engine import SlideRenderer
from src.renderer.styles import load_style_config
from src.services.credit_service import refund_credits
from src.storage.s3 import S3Client

logger = logging.getLogger(__name__)


class CarouselService:
    def __init__(self) -> None:
        self.copywriter = AnthropicCopywriter()
        self.image_provider = GeminiImageProvider()
        self.s3 = S3Client()

    async def generate_and_send(
        self,
        user_id: int,
        telegram_chat_id: int,
        input_text: str,
        style_slug: str,
        status_message_id: int,
    ) -> None:
        # Input validation
        if len(input_text) > MAX_INPUT_TEXT_LENGTH:
            raise ValueError(f"Input text exceeds maximum length of {MAX_INPUT_TEXT_LENGTH}")
        if style_slug not in AVAILABLE_STYLES:
            raise ValueError(f"Unknown style slug: {style_slug}")

        settings = get_settings()
        bot_token = settings.telegram.bot_token.get_secret_value()
        factory = get_session_factory()

        async with factory() as session:
            # Create DB record
            generation = CarouselGeneration(
                user_id=user_id,
                input_text=input_text,
                style_slug=style_slug,
                status=GenerationStatus.PENDING,
            )
            session.add(generation)
            await session.commit()

            try:
                # Step 1: AI Copywriting
                generation.status = GenerationStatus.COPYWRITING
                await session.commit()

                slide_count = min(
                    max(MIN_SLIDES_PER_CAROUSEL, len(input_text) // 500 + 3),
                    MAX_SLIDES_PER_CAROUSEL,
                )
                slides_content = await self.copywriter.generate_slides(
                    input_text=input_text,
                    style_slug=style_slug,
                    slide_count=slide_count,
                )

                # Enforce slide count limits after AI returns
                slides_content = slides_content[:MAX_SLIDES_PER_CAROUSEL]
                generation.slide_count = len(slides_content)

                # Step 2: Image Generation
                generation.status = GenerationStatus.IMAGE_GENERATION
                await session.commit()

                bg_images: list[bytes | None] = []
                for sc in slides_content:
                    bg = await self.image_provider.generate_background(
                        style_slug=style_slug,
                        slide_heading=sc.heading,
                        slide_position=sc.position,
                    )
                    bg_images.append(bg)

                # Step 3: Rendering
                generation.status = GenerationStatus.RENDERING
                await session.commit()

                style_config = load_style_config(style_slug)
                renderer = SlideRenderer(style_config)
                rendered_slides: list[bytes] = []

                for i, sc in enumerate(slides_content):
                    bg = bg_images[i]
                    png_bytes = renderer.render(
                        heading=sc.heading,
                        body_text=sc.body_text,
                        background_image=bg,
                    )
                    rendered_slides.append(png_bytes)

                # Step 4: Upload to S3
                generation.status = GenerationStatus.UPLOADING
                await session.commit()

                ts = int(time.time())
                for i, (sc, png_bytes) in enumerate(
                    zip(slides_content, rendered_slides, strict=True)
                ):
                    s3_key = f"{S3_CAROUSEL_PREFIX}/{user_id}/{generation.id}/{ts}_slide_{i}.png"
                    self.s3.upload_bytes(s3_key, png_bytes)

                    slide = Slide(
                        carousel_id=generation.id,
                        position=sc.position,
                        heading=sc.heading,
                        body_text=sc.body_text,
                        rendered_s3_key=s3_key,
                    )
                    session.add(slide)

                await session.commit()

                # Step 5: Send to Telegram via direct API (no aiogram import in worker)
                generation.status = GenerationStatus.SENDING
                await session.commit()

                async with httpx.AsyncClient() as http:
                    # Send slides as photo group
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

                # Refund credits on failure
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

                # Notify user of failure
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

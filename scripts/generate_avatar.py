"""One-shot script: generate bot avatar via Gemini and save to assets/avatar.png."""

from __future__ import annotations

import asyncio
import io
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

from src.config.settings import get_settings

AVATAR_SIZE = 640
PROMPT = (
    "Cute cartoon banana character mascot, wearing cool sunglasses, confident smirk, "
    "holding a phone showing carousel slides. Black background #1A1A1A, vibrant yellow "
    "banana #FFD600, minimal flat design, bold and energetic vibe. Icon style, centered "
    "composition, no text, suitable for circular crop as Telegram bot avatar. 640x640px."
)
OUTPUT_PATH = Path("assets/avatar.png")


async def main() -> None:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini.api_key.get_secret_value())

    print(f"Generating avatar with model {settings.gemini.model}...")
    response = await client.aio.models.generate_content(
        model=settings.gemini.model,
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    # Extract image bytes
    candidates = getattr(response, "candidates", None)
    if not candidates:
        print("ERROR: Gemini returned no candidates", file=sys.stderr)
        sys.exit(1)

    image_data: bytes | None = None
    content = candidates[0].content
    if content and content.parts:
        for part in content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                image_data = part.inline_data.data
                break

    if image_data is None:
        print("ERROR: No image in Gemini response", file=sys.stderr)
        sys.exit(1)

    # Process: resize to 640x640, ensure RGB PNG
    img = Image.open(io.BytesIO(image_data))
    if img.size != (AVATAR_SIZE, AVATAR_SIZE):
        img = img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH, format="PNG", optimize=True)
    print(f"Avatar saved to {OUTPUT_PATH} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    asyncio.run(main())

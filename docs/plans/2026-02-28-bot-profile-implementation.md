# Bot Profile Setup — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the Telegram bot profile (name, bio, description, menu commands, avatar) programmatically via Bot API on startup.

**Architecture:** All profile settings are applied in the FastAPI lifespan (`src/api/app.py`) after bot creation, using aiogram's Bot API methods (`set_my_name`, `set_my_description`, `set_my_short_description`, `set_my_commands`). Avatar is generated once via Gemini, saved to `assets/`, and set via `set_chat_photo` (or manually via BotFather).

**Tech Stack:** aiogram 3.17+, Gemini (google-genai), Pillow, FastAPI lifespan

---

### Task 1: Update bot menu commands to Russian

The `set_my_commands` call already exists in `src/api/app.py:32-40` but with English descriptions. Update to Russian.

**Files:**
- Modify: `src/api/app.py:32-40`

**Step 1: Update command descriptions**

In `src/api/app.py`, replace the existing `set_my_commands` block:

```python
    # Set bot commands menu
    await bot.set_my_commands(
        [
            BotCommand(command="generate", description="Создать карусель"),
            BotCommand(command="styles", description="Стили оформления"),
            BotCommand(command="credits", description="Мой баланс"),
            BotCommand(command="buy", description="Купить кредиты"),
            BotCommand(command="help", description="Помощь"),
        ]
    )
```

**Step 2: Run existing tests to verify nothing breaks**

Run: `make test`
Expected: All tests pass (no tests directly exercise `set_my_commands`, but lifespan mocking shouldn't break).

**Step 3: Commit**

```bash
git add src/api/app.py
git commit -m "feat: update bot menu commands to Russian"
```

---

### Task 2: Add bot profile setup (name, bio, description) to lifespan

Use aiogram Bot API methods to set the profile texts on startup.

**Files:**
- Modify: `src/api/app.py` (lifespan function, after `set_my_commands`)

**Step 1: Add profile setup calls after `set_my_commands`**

Add these lines right after the `set_my_commands` block in `src/api/app.py`:

```python
    # Set bot profile texts
    await bot.set_my_name(name="Карусель-мейкер")
    await bot.set_my_short_description(
        short_description="🍌 Делаю карусели для LinkedIn и Instagram. Просто скинь текст — остальное на мне."
    )
    await bot.set_my_description(
        description=(
            "🍌 Текст → виральная карусель за минуту.\n"
            "\n"
            "Что умеет:\n"
            "• AI-копирайтинг для слайдов\n"
            "• 10 стилей оформления\n"
            "• AI-генерация изображений\n"
            "• Готовые PNG 1080×1350\n"
            "\n"
            "3 бесплатных карусели при старте.\n"
            "Жми «Запустить» 🚀"
        )
    )
    logger.info("Bot profile configured")
```

**Step 2: Run tests**

Run: `make test`
Expected: All tests pass.

**Step 3: Commit**

```bash
git add src/api/app.py
git commit -m "feat: set bot name, bio, and description on startup"
```

---

### Task 3: Generate bot avatar via Gemini

Generate a mascot avatar image using the Gemini API and save it to `assets/`.

**Files:**
- Create: `scripts/generate_avatar.py`

**Step 1: Write the avatar generation script**

```python
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
```

**Step 2: Run the script to generate the avatar**

Run: `uv run python -m scripts.generate_avatar`
Expected: `Avatar saved to assets/avatar.png (640x640)`

Verify the file exists: `ls -la assets/avatar.png`

**Step 3: Visually inspect the generated image**

Open `assets/avatar.png` and check it looks like a cartoon banana mascot on dark background. If not satisfactory, re-run or tweak the prompt.

**Step 4: Commit**

```bash
git add scripts/generate_avatar.py assets/avatar.png
git commit -m "feat: add generated bot avatar"
```

---

### Task 4: Set bot avatar via Bot API (optional, can also do via BotFather)

Add avatar upload to the lifespan. This only needs to run once — the avatar persists on Telegram servers.

**Files:**
- Modify: `src/api/app.py`

**Step 1: Add conditional avatar upload**

After the profile texts block in lifespan, add:

```python
    # Set bot avatar (one-time — Telegram persists it)
    avatar_path = Path("assets/avatar.png")
    if avatar_path.exists():
        from aiogram.types import FSInputFile

        try:
            await bot.set_chat_photo(
                chat_id=bot.id,  # bot's own "chat" for profile photo
                photo=FSInputFile(avatar_path),
            )
            logger.info("Bot avatar set from %s", avatar_path)
        except Exception:
            # set_chat_photo may not work for bot profile in all cases;
            # fall back to setting via BotFather manually
            logger.debug("Could not set bot avatar via API — set it via BotFather instead")
```

Add `from pathlib import Path` to the imports at the top of the file.

**Note:** Telegram's `setChatPhoto` for bots' own profile is not always supported via Bot API. If it fails, the avatar should be set manually via BotFather. The try/except handles this gracefully.

**Step 2: Run tests**

Run: `make test`
Expected: All tests pass.

**Step 3: Commit**

```bash
git add src/api/app.py
git commit -m "feat: attempt to set bot avatar on startup with fallback"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Russian menu commands | `src/api/app.py` |
| 2 | Bot name + bio + description | `src/api/app.py` |
| 3 | Generate avatar image | `scripts/generate_avatar.py`, `assets/avatar.png` |
| 4 | Upload avatar on startup | `src/api/app.py` |

After implementation, the bot profile will be fully configured on every startup: Russian menu commands, name "Карусель-мейкер", bio with emoji, structured description, and mascot avatar.

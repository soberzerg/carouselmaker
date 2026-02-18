# Code Review Agent Memory

## Project Structure
- Python 3.13, FastAPI + aiogram 3.17+ Telegram bot, SQLAlchemy 2.x async, Celery + Redis, PostgreSQL 16
- Source: `src/` with models/, schemas/, api/, bot/, ai/, renderer/, services/, worker/
- Style presets: JSON configs in `assets/templates/` (nano_banana, minimalist, tech, corporate)
- Rendering: Pillow-based in `src/renderer/engine.py`, layout in `src/renderer/layout.py`
- AI: Anthropic for copywriting (`src/ai/anthropic_provider.py`), Gemini for image gen (`src/ai/gemini_provider.py`)
- Celery tasks wrap async code via `asyncio.run()` in `src/worker/tasks/`

## Patterns & Conventions
- Settings: pydantic-settings with nested config groups (db, redis, s3, telegram, anthropic, gemini, yookassa)
- `get_settings()` is `@lru_cache(maxsize=1)` singleton
- Style configs: `@dataclass` (`StyleConfig`) loaded from JSON via `@lru_cache` (`load_style_config`)
- Schemas: Pydantic v2 with `from_attributes = True` for ORM models
- Enums: `StrEnum` used for `TextPosition`, `SlideType` in schemas
- DB models use `TimestampMixin` base + SQLAlchemy `Mapped[]` type hints
- Migration: Alembic autogenerate, manual revision IDs sometimes used
- Worker sends Telegram messages via direct HTTP API (httpx), not aiogram
- `completed_counter: list[int]` pattern used as mutable counter in async gather

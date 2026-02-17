# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nano Banana Carousel Maker** — a SaaS platform for AI-powered generation of viral carousels for LinkedIn and Instagram. Users input text and get professional slides in minutes. Flagship feature: "Nano Banana" brand style (high-contrast yellow-black).

PRD is in `Carousel PRD.md` (in Russian).

## Development Phases

- **MVP (Phase 1):** Telegram bot — credit system, quick text-to-carousel generation, AI copywriting + image generation, style presets (Minimalist, Tech, Corporate, Nano Banana), PNG export (1080x1350)
- **Phase 2:** Web app — React frontend, wizard flow, carousel editor, custom styles, ZIP export, team access, analytics

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot Framework | aiogram 3.17+ |
| Web Framework | FastAPI 0.115+ |
| Language | Python 3.13 |
| Package Manager | UV |
| Build System | Hatchling |
| Database | PostgreSQL 16 (asyncpg + psycopg2-binary) |
| ORM | SQLAlchemy 2.x (async) + Alembic |
| Async Tasks | Celery 5.4 + Redis 7 |
| AI Copywriting | Anthropic Claude (claude-sonnet-4-20250514) |
| AI Image Gen | Google Gemini (gemini-2.0-flash-exp) |
| Rendering | Pillow 11 |
| HTTP Client | httpx |
| Containerization | Docker & Docker Compose |
| Storage | S3-compatible (MinIO / AWS) via boto3 |
| Payments | YooKassa (stub) |
| Config | pydantic-settings |

## Build & Run Commands

```bash
# Install dependencies
make install              # uv sync --extra dev

# Start infrastructure (postgres, redis, minio)
make up

# Run FastAPI dev server (port 8000)
make dev

# Run Celery worker
make worker

# Run Celery beat scheduler
make beat

# Database migrations
make migrate              # Apply migrations (alembic upgrade head)
make revision MSG="msg"   # Create new migration (autogenerate)
make downgrade            # Rollback one migration

# Quality
make lint                 # ruff check + mypy
make format               # ruff fix + format
make test                 # pytest
make test-cov             # pytest with coverage

# Docker (full stack)
make up-all               # Start all services including app + worker
make down                 # Stop all services
```

## Project Structure

```
src/
├── main.py                          # Entrypoint: uvicorn FastAPI app
├── config/
│   ├── settings.py                  # pydantic-settings (nested: db, redis, s3, telegram, anthropic, gemini, yookassa)
│   └── constants.py                 # App-wide constants
├── models/                          # SQLAlchemy ORM models
│   ├── base.py                      # Declarative Base
│   ├── user.py                      # User (with denormalized credit_balance)
│   ├── carousel.py                  # CarouselGeneration + GenerationStatus enum
│   ├── slide.py                     # Slide
│   ├── credit.py                    # CreditTransaction + TransactionType enum
│   └── style_preset.py             # StylePreset
├── schemas/                         # Pydantic request/response schemas
│   ├── user.py, credit.py, carousel.py, slide.py, style.py
├── db/
│   ├── session.py                   # Async session factory
│   └── repository.py               # Generic CRUD repository
├── api/
│   ├── app.py                       # FastAPI app factory
│   ├── dependencies.py              # DI (settings, DB session)
│   └── routers/
│       ├── health.py                # GET /health
│       ├── webhook.py               # POST /webhook/telegram
│       ├── admin.py                 # Admin endpoints (API-key protected)
│       └── payments.py              # YooKassa webhook
├── bot/
│   ├── factory.py                   # aiogram Dispatcher + Router setup
│   ├── handlers/
│   │   ├── start.py                 # /start command
│   │   ├── generate.py              # Carousel generation flow
│   │   ├── styles.py                # Style selection
│   │   ├── credits.py               # Credit balance & purchase
│   │   └── callbacks.py             # Inline callback handlers
│   ├── keyboards/
│   │   ├── inline.py                # Inline keyboards
│   │   └── reply.py                 # Reply keyboards
│   ├── middlewares/
│   │   ├── auth.py                  # User registration/lookup middleware
│   │   └── throttle.py              # Rate limiting (Redis-backed)
│   └── states/
│       └── generation.py            # FSM states for generation flow
├── ai/
│   ├── base.py                      # Abstract provider interfaces
│   ├── prompts.py                   # Prompt templates
│   ├── anthropic_provider.py        # Claude copywriting provider
│   └── gemini_provider.py           # Gemini image generation provider
├── renderer/
│   ├── engine.py                    # Pillow-based slide renderer (1080x1350 PNG)
│   ├── layout.py                    # Slide layout calculations
│   └── styles.py                    # Style application logic
├── storage/
│   └── s3.py                        # S3/MinIO client (boto3)
├── payments/
│   ├── base.py                      # Abstract payment provider
│   └── yookassa_provider.py         # YooKassa implementation (stub)
├── services/                        # Business logic layer
│   ├── user_service.py
│   ├── credit_service.py
│   ├── carousel_service.py
│   └── style_service.py
└── worker/
    ├── celery_app.py                # Celery app configuration
    └── tasks/
        ├── generate_carousel.py     # Main carousel generation task
        └── cleanup.py               # Periodic cleanup task

assets/
├── fonts/                           # Custom fonts (.gitkeep)
└── templates/                       # Style preset JSON configs
    ├── nano_banana.json
    ├── minimalist.json
    ├── tech.json
    └── corporate.json

alembic/
├── env.py                           # Alembic environment config
└── versions/                        # Migration files

docker/
├── docker-compose.yml               # All services (postgres, redis, minio, app, worker)
├── Dockerfile                       # FastAPI app image
└── Dockerfile.worker                # Celery worker image

tests/
├── conftest.py                      # Shared fixtures (aiosqlite for DB)
├── test_api/
│   └── test_health.py
├── test_handlers/
│   └── test_start.py
├── test_renderer/
│   └── test_engine.py
└── test_services/
    ├── test_user_service.py
    └── test_credit_service.py
```

## Key Architecture Notes

- **Webhook mode:** Bot receives updates via FastAPI POST `/webhook/telegram`
- **Celery async bridge:** Celery tasks use `asyncio.run()` wrapper since Celery 5.4 doesn't support async natively
- **Decoupled services:** `CarouselService` is independent of bot/API — reusable in Phase 2
- **Credit system:** Denormalized `credit_balance` on User model; `SELECT FOR UPDATE` prevents double-spend
- **Worker sends results:** Celery worker sends carousel via direct Telegram HTTP API (httpx), not aiogram
- **Style presets:** JSON configs in `assets/templates/`, loaded by renderer
- **Settings:** Nested pydantic-settings — `Settings.db`, `Settings.redis`, `Settings.s3`, etc.
- **Bot middlewares:** Auth middleware auto-registers users; throttle middleware uses Redis for rate limiting

## Agent Usage

Claude Code has specialized agents (subagent types) that should be used for specific tasks in this project:

| Agent | When to use |
|-------|-------------|
| `telegram-backend-architect` | **Primary agent for Phase 1.** Any backend work: bot handlers, FastAPI endpoints, SQLAlchemy models, Alembic migrations, Celery tasks, Docker Compose, Redis caching, DI wiring. Matches our full stack: aiogram + FastAPI + PostgreSQL + Redis + Celery + SQLAlchemy + Alembic + UV + Docker. |
| `react-dev` | **Phase 2 frontend.** React components, pages, routing, Tailwind styling, Shadcn UI, i18n setup. Use when building the web app. |
| `code-review` | Review recent git changes, PR diffs, or newly written code before committing. |
| `refactor-after-review` | Apply code review feedback — restructure code, fix patterns, extract modules. |
| `prd-writer` | Create or update Product Requirements Documents. PRD is in `Carousel PRD.md`. |
| `Explore` | Deep codebase exploration when simple Grep/Glob isn't enough. |
| `Plan` | Design implementation strategy for complex multi-file features before writing code. |

### Rules

- For any backend task (models, handlers, endpoints, tasks, Docker, migrations) — always prefer `telegram-backend-architect`
- For frontend tasks (Phase 2) — always prefer `react-dev`
- After finishing a feature, run `code-review` before committing
- When a review has comments to address, use `refactor-after-review`
- Use `Plan` agent before starting complex features that touch 3+ layers (e.g., new entity end-to-end)

## Environment Variables

Copy `.env.example` to `.env` and fill in API keys. Key groups:

| Group | Variables |
|-------|-----------|
| Database | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` |
| Redis | `REDIS_URL` |
| S3/MinIO | `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION` |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_URL`, `TELEGRAM_WEBHOOK_SECRET` |
| AI | `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` |
| Payments | `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, `YOOKASSA_WEBHOOK_SECRET` |
| App | `APP_ENV`, `APP_DEBUG`, `APP_LOG_LEVEL`, `ADMIN_API_KEY` |

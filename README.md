# Nano Banana Carousel Maker

AI-powered carousel generation for LinkedIn & Instagram via Telegram bot.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.13+ with [UV](https://docs.astral.sh/uv/)

### Setup

```bash
# Clone and enter the project
cd carouselmaker

# Copy environment config
cp .env.example .env
# Edit .env with your API keys (Telegram bot token, Anthropic, Gemini)

# Start all services
make up

# Run database migrations
make migrate

# Start the dev server (with hot reload)
make dev

# In another terminal — start the Celery worker
make worker
```

### Available Commands

```bash
make up         # Start Docker services (postgres, redis, minio)
make down       # Stop Docker services
make dev        # Run FastAPI dev server with hot reload
make worker     # Run Celery worker
make beat       # Run Celery beat scheduler
make migrate    # Apply Alembic migrations
make revision   # Create new Alembic migration (MSG="description")
make lint       # Run ruff + mypy
make test       # Run pytest
make format     # Auto-format with ruff
```

### Bot Commands

| Command     | Description                          |
|-------------|--------------------------------------|
| `/start`    | Welcome message + free credits       |
| `/generate` | Create a new carousel                |
| `/styles`   | Browse style presets                 |
| `/credits`  | Check credit balance                 |
| `/buy`      | Purchase credit packs                |
| `/help`     | Show help message                    |

## Architecture

```
Telegram → Webhook → FastAPI → aiogram dispatcher
                                    ↓
                              Celery task
                                    ↓
                     AI Copywriting (Claude) → Slide text
                     AI Image Gen (Gemini)   → Background
                     Renderer (Pillow)       → PNG slides
                     S3 Upload (MinIO)       → Storage
                                    ↓
                          Send carousel to user
```

## Style Presets

- **Nano Banana** — High-contrast yellow (#FFD600) on black (#1A1A1A)
- **Minimalist** — Clean white/grey with modern typography
- **Tech** — Dark blue with cyan accents
- **Corporate** — Navy blue with white text

## Project Structure

```
src/
├── api/          # FastAPI app, routers, dependencies
├── bot/          # aiogram handlers, keyboards, middlewares, FSM states
├── ai/           # AI provider interfaces (Claude, Gemini)
├── renderer/     # Pillow-based slide renderer
├── services/     # Business logic layer
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response schemas
├── db/           # Database session & repository
├── storage/      # S3 client
├── payments/     # Payment provider (YooKassa stub)
└── worker/       # Celery tasks
```

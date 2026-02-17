.PHONY: up down up-all dev worker beat migrate revision downgrade lint format test test-cov install

# ── Docker ────────────────────────────────────────────────
up:
	docker compose -f docker/docker-compose.yml up -d postgres redis minio

down:
	docker compose -f docker/docker-compose.yml down

up-all:
	docker compose -f docker/docker-compose.yml up -d

# ── Development ───────────────────────────────────────────
dev:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	uv run celery -A src.worker.celery_app worker --loglevel=info --concurrency=2

beat:
	uv run celery -A src.worker.celery_app beat --loglevel=info

# ── Database ──────────────────────────────────────────────
migrate:
	uv run alembic upgrade head

revision:
ifndef MSG
	$(error MSG is required. Usage: make revision MSG="your migration message")
endif
	uv run alembic revision --autogenerate -m "$(MSG)"

downgrade:
	uv run alembic downgrade -1

# ── Quality ───────────────────────────────────────────────
lint:
	uv run ruff check src/ tests/
	uv run mypy src/

format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

# ── Testing ───────────────────────────────────────────────
test:
	uv run pytest tests/ -v --tb=short

test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

# ── Setup ─────────────────────────────────────────────────
install:
	uv sync --extra dev

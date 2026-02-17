# ── Builder stage ─────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY src/__init__.py src/__init__.py
RUN uv sync --frozen --no-dev --no-editable

# Copy application code
COPY src/ src/
COPY assets/ assets/
COPY alembic/ alembic/
COPY alembic.ini ./

# ── Runtime stage ─────────────────────────────────────────
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# System deps for Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 libjpeg62-turbo libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/assets /app/assets
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

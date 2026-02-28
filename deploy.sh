#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/var/www/carouselmaker"
COMPOSE_FILE="docker/docker-compose.yml"

cd "$PROJECT_DIR"

echo "=== Carouselmaker Deploy ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Pull latest code
echo "--- git pull ---"
git pull --ff-only
echo ""

# 2. Rebuild and restart Docker services
echo "--- docker compose build ---"
docker compose -f "$COMPOSE_FILE" build
echo ""

echo "--- docker compose up ---"
docker compose -f "$COMPOSE_FILE" up -d
echo ""

# 3. Wait for app container to be healthy before running migrations
echo "--- waiting for app to be healthy ---"
ATTEMPTS=0
MAX_ATTEMPTS=30
until docker compose -f "$COMPOSE_FILE" exec app python -c "print('ok')" &>/dev/null; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
        echo "ERROR: app container failed to start after ${MAX_ATTEMPTS} attempts"
        docker compose -f "$COMPOSE_FILE" logs app --tail=30
        exit 1
    fi
    echo "  waiting... ($ATTEMPTS/$MAX_ATTEMPTS)"
    sleep 2
done
echo "  app is ready"
echo ""

# 4. Run Alembic migrations inside the app container
echo "--- alembic upgrade head ---"
docker compose -f "$COMPOSE_FILE" exec app alembic upgrade head
echo ""

echo "=== Deploy complete ==="
docker compose -f "$COMPOSE_FILE" ps

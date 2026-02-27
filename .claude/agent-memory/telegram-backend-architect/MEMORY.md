# Telegram Backend Architect - Memory

## Project: Nano Banana Carousel Maker

### Database & Migrations
- PostgreSQL enum types created by SQLAlchemy use enum **member names** (PENDING, SUCCEEDED) as PG values, NOT `.value` strings (pending, succeeded). Do NOT use `server_default="pending"` with `Enum(PaymentStatus)` -- it will fail. Either omit `server_default` (preferred, matches existing `generation_status` pattern) or use uppercase.
- Existing pattern: `CarouselGeneration.status` uses `Enum(GenerationStatus, name="generation_status")` with `default=` only, no `server_default`
- Always add `op.execute("DROP TYPE IF EXISTS ...")` in migration downgrade for custom enum types
- Alembic env.py imports from `src.models import Base` which triggers all model registrations

### Code Patterns
- Ruff B008: FastAPI `Depends()` in function args uses `# noqa: B008` (see admin.py pattern)
- Ruff B904: Always `raise ... from exc` inside except clauses
- Auth middleware injects `db_user: User` and `db_session: AsyncSession` into handler data
- DB session lifecycle: middleware creates session, commits on success, rolls back on error
- Telegram notifications from non-bot code (webhooks, workers): use httpx direct API call to `api.telegram.org/bot{token}/sendMessage`

### Payment Integration (YooKassa)
- Payment model: `src/models/payment.py` with PaymentStatus enum (PENDING/SUCCEEDED/CANCELED)
- YooKassa uses HTTP Basic Auth (shop_id:secret_key), NOT API keys
- Every create_payment needs unique `Idempotence-Key` header (UUID4)
- Webhook verification: re-fetch payment from API (no HMAC signatures)
- Payment amounts: strings with 2 decimal places ("149.00")
- `capture: true` for immediate capture
- Metadata carries `user_id` and `credit_amount` as strings
- Flow: bot callback creates YooKassa payment + DB record (PENDING) -> user pays -> webhook updates status + credits user

### Settings
- Nested pydantic-settings: `Settings.yookassa.shop_id`, `.secret_key`, `.return_url`
- Environment prefix: `YOOKASSA_` (so `YOOKASSA_RETURN_URL` maps to `return_url`)

### File Locations
- Models: `src/models/` (registered in `src/models/__init__.py`)
- Payments: `src/payments/base.py` (PaymentResult dataclass + PaymentProvider ABC), `src/payments/yookassa_provider.py`
- Webhook: `src/api/routers/payments.py` POST `/webhook/yookassa`
- Bot callbacks: `src/bot/handlers/callbacks.py` (`buy:` prefix)
- Credit service: `src/services/credit_service.py` (`purchase_credits` with SELECT FOR UPDATE)

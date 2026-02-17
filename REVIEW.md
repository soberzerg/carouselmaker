# Code Review: Nano Banana Carousel Maker

Reviewed all 95 files across 4 review areas. Found **13 Critical**, **35 Major**, **42 Minor**, and **20 Nit** issues.

---

## CRITICAL (must fix before any deployment)

| # | Area | Issue |
|---|------|-------|
| **C1** | Services | **No credit refund on generation failure.** Credits are charged in the bot handler, then Celery task runs. If generation fails, credits are gone forever. `TransactionType.REFUND` exists but no `refund_credits()` function. |
| **C2** | Worker | **Celery task swallows exceptions.** `generate_carousel_task` catches all exceptions and returns `{"status": "failed"}` — Celery marks the task as SUCCESS. No retry, no monitoring visibility. |
| **C3** | Services | **Telegram `sendMediaGroup` response never checked.** Generation is marked COMPLETED even if Telegram rejects the request (file too large, bot blocked, etc.). |
| **C4** | Bot | **Session rollback missing in AuthMiddleware.** If a handler crashes after `SELECT FOR UPDATE`, the row lock is held until session GC/timeout — potential deadlocks. |
| **C5** | Config | **`get_settings()` not cached.** Called everywhere (session.py, celery_app.py, every AI provider `__init__`), re-parses `.env` each time. Use `@lru_cache`. |
| **C6** | DB | **`get_async_session` never commits or rolls back.** Combined with Repository's `flush()` (not `commit()`), data is silently lost. |
| **C7** | DB | **Bottom-of-file circular imports are unnecessary and fragile.** All 4 model files do `from src.models.X import Y # noqa` at the bottom. String-based `relationship("User")` + `from __future__ import annotations` already handle this. |
| **C8** | Security | **Timing-unsafe secret comparisons.** Webhook secret, API key, and YooKassa signature all use `!=` instead of `hmac.compare_digest()`. Vulnerable to timing attacks. |
| **C9** | Config | **Module-level `Settings()` in `db/session.py`.** Engine is created at import time — tests cannot override settings; imports trigger DB connection attempts. |
| **C10** | Tests | **SQLite test DB vs PostgreSQL-specific features.** Models use `Enum(..., name=...)` and `JSONB` (StylePreset) — these don't exist in SQLite. Tests pass but don't exercise real schema. Also uses file-based `test.db` instead of in-memory. |
| **C11** | Services | **Race condition in `get_or_create_user`.** Two concurrent messages from a new user both see `None`, both INSERT — one gets `UniqueViolation`. No `ON CONFLICT` or retry. |
| **C12** | Bot | **Credit check and charge are on different sessions.** `/generate` checks balance on one session, then `on_text_received` charges on another (from a later event). The initial check is stale. `charge_credits` has `SELECT FOR UPDATE` which is the real guard, but UX is misleading. |
| **C13** | Services | **`sendMediaGroup` 10-photo limit not enforced.** `MAX_SLIDES_PER_CAROUSEL=10` matches Telegram's limit, but nothing prevents the AI from returning more slides than requested. |

---

## MAJOR (should fix before beta)

| # | Area | Issue |
|---|------|-------|
| **M1** | DB | **No cascade deletes.** Relationships lack `cascade="all, delete-orphan"`, ForeignKeys lack `ondelete="CASCADE"`. Deleting a User/Carousel will violate FK constraints. |
| **M2** | DB | **`lazy="selectin"` on User relationships.** Every user fetch eagerly loads ALL credit_transactions and carousel_generations — unbounded memory as data grows. |
| **M3** | DB | **`credit_balance` uses Python-side `default=0`**, not `server_default`. Direct SQL inserts fail. |
| **M4** | Bot | **Credit charge + Celery dispatch not atomic.** If commit succeeds but Celery broker is down, credits gone with no carousel. |
| **M5** | Bot | **ThrottleMiddleware not on callback_query.** Users can spam inline buttons (including stub payment `buy:N`) without rate limiting. |
| **M6** | Bot | **No validation of `style_slug`** from callback data against `AVAILABLE_STYLES`. Crafted callback can inject arbitrary slugs. |
| **M7** | Bot | **`int(pack_index)` with no try/except.** `buy:abc` crashes the handler. |
| **M8** | Bot | **`generating` FSM state is set then immediately cleared** — serves no purpose, provides no protection during async generation. |
| **M9** | AI | **No JSON parsing error handling in AnthropicCopywriter.** `json.loads()` will fail on markdown fences, preamble text — common LLM failure mode. |
| **M10** | AI | **No error handling for Gemini API failures.** Rate limits, quota exceeded, safety blocks — all propagate unhandled. |
| **M11** | AI | **`response.candidates[0]` can be empty** (Gemini safety filter). `IndexError` at runtime, hidden by `type: ignore`. |
| **M12** | Storage | **`_ensure_bucket` catches ALL `ClientError`**, not just 404. Auth failures trigger a `create_bucket` that also fails with a confusing error. |
| **M13** | Storage | **`list_objects` has no pagination.** Only returns first 1000 keys. Cleanup task will miss files beyond that. |
| **M14** | Worker | **`asyncio.run()` per task** creates/destroys event loop each time. Module-level asyncpg engine from forked process may be unsafe. |
| **M15** | Worker | **Cleanup deletes S3 files but doesn't update DB records.** `Slide.rendered_s3_key` still references deleted files — broken links. |
| **M16** | Worker | **`task_acks_late=True` without idempotency.** Killed worker causes re-delivery, creating duplicate carousels + double-charging credits. |
| **M17** | Docker | **No non-root user in Dockerfiles.** Containers run as root. |
| **M18** | Docker | **No health checks for app/worker containers.** Orchestrators can't detect unhealthy state. |
| **M19** | API | **Readiness endpoint crashes with stack trace** if DB is unreachable. Should return 503 with structured error. |
| **M20** | Config | **Nested `BaseSettings` don't inherit `.env` from parent `Settings`.** `DatabaseSettings()` only sees real env vars, not `.env` file values. Works if `python-dotenv` is installed (it is, via pydantic-settings), but fragile. |
| **M21** | Bot | **Two separate Redis connections** (RedisStorage + ThrottleMiddleware) — `ThrottleMiddleware.redis` is never closed. |
| **M22** | Services | **No input validation in `CarouselService`** — `input_text` length and `style_slug` validity not checked. Direct Celery dispatch bypasses bot-level validation. |
| **M23** | Security | **Default secrets in config.** `webhook_secret="change-me"`, `admin_api_key="change-me"` — no validation that they've been changed in production. |

---

## MINOR (should fix for production quality)

| # | Area | Issue |
|---|------|-------|
| m1 | DB | Missing `UniqueConstraint("carousel_id", "position")` on Slide — duplicates possible |
| m2 | DB | `generate_uuid` in base.py is dead code — defined, never used |
| m3 | DB | No FK relationship between `CarouselGeneration.style_slug` and `StylePreset.slug` |
| m4 | DB | `onupdate=func.now()` on `updated_at` is Python-side only; direct SQL bypasses it |
| m5 | DB | Repository `update()` uses `setattr` with no validation of attribute names |
| m6 | DB | Repository `get_all()` uses `LIMIT`/`OFFSET` without `ORDER BY` — non-deterministic pagination |
| m7 | DB | Schemas import enums directly from model layer (tight coupling) |
| m8 | DB | `updated_at` missing from all read schemas |
| m9 | DB | `StylePreset.slug` has redundant `index=True` alongside `unique=True` (double index) |
| m10 | Renderer | `calculate_text_height` in layout.py is dead code — never called |
| m11 | Renderer | Text can overflow slide vertically — no truncation or font size reduction |
| m12 | Renderer | Heading text is always left-aligned — alignment should be a `StyleConfig` property |
| m13 | Renderer | Hardcoded `gap = 40` between heading and body — should be in `StyleConfig` |
| m14 | Renderer | `_hex_to_rgb` does not validate input — invalid hex causes confusing `ValueError` |
| m15 | Renderer | Single word wider than `max_width` extends beyond right edge — no hyphenation/truncation |
| m16 | Renderer | Style config JSON re-read from disk every call — should cache with `@lru_cache` |
| m17 | Renderer | `ASSETS_DIR` path assumes project structure — breaks if file is moved or installed as package |
| m18 | Renderer | `load_style_config` manually maps every field with `.get()` — fragile if `StyleConfig` grows |
| m19 | AI | Prompt injection vulnerability — user `input_text` injected into prompt without sanitization |
| m20 | AI | Slide count is a suggestion, not enforced — LLM can return more/fewer slides |
| m21 | AI | `response.content[0].text` assumes non-empty content — `IndexError` if safety filter triggers |
| m22 | AI | No request timeout configured on Anthropic client (default: 10 min) |
| m23 | AI | Silent fallback to `b""` for image generation failure is a sentinel value anti-pattern |
| m24 | Storage | Synchronous boto3 in async codebase — blocks event loop during S3 operations |
| m25 | Storage | `create_bucket` missing `CreateBucketConfiguration` for non-us-east-1 regions |
| m26 | Payments | YooKassa stub `verify_webhook` always returns True — no guard against production use |
| m27 | Worker | `CarouselService` instantiated per task — new AI clients + S3 client each time, no connection reuse |
| m28 | Worker | Cleanup task timestamp parsing is fragile — assumes specific S3 key format |
| m29 | Worker | Cleanup task has no retry configuration — S3 failure means 24h wait for next attempt |
| m30 | Bot | No `bot.set_my_commands()` — users don't see command autocomplete in Telegram |
| m31 | Bot | `callback.message` accessed with `type: ignore` — can genuinely be `None` for old messages |
| m32 | Bot | `on_cancel` handler not scoped to FSM states — catches all `cancel` callbacks globally |
| m33 | Bot | No handler for unexpected messages during FSM states (e.g., photo sent in `waiting_text`) |
| m34 | Bot | Reply keyboard uses raw `/command` text as button labels — poor UX |
| m35 | Bot | Rate limiter records throttled messages — extends lockout beyond window |
| m36 | Bot | `time.time()` as sorted set member — collisions on rapid requests weaken rate limiter |
| m37 | Config | DB password not URL-encoded — special chars break connection string |
| m38 | Config | `app_debug` setting exists but is never used |
| m39 | Config | `DBSession = Depends(get_db_session)` alias defined but never used |
| m40 | Docker | `.env.example` has `localhost` but Docker Compose needs service names (`postgres`, `redis`) |
| m41 | Docker | Ports 5432/6379/9000 exposed to `0.0.0.0` — should bind to `127.0.0.1` for dev |
| m42 | Docker | MinIO has no health check but `app`/`worker` depend on it with `service_started` |

---

## NIT

| # | Area | Issue |
|---|------|-------|
| n1 | DB | `do_run_migrations` in alembic/env.py has `type: ignore` instead of proper type annotation |
| n2 | DB | `TimestampMixin` not exported in `models/__init__.py` `__all__` |
| n3 | DB | PEP 695 generic syntax `Repository[T: Base]` requires Python 3.12+ (fine for target 3.13) |
| n4 | Bot | `STYLE_DISPLAY_NAMES` lives in `keyboards/inline.py` but imported by `handlers/styles.py` — should be shared |
| n5 | Bot | `GenerationFSM.generating` state defined but never meaningfully used |
| n6 | Bot | Inconsistent handler naming: `cmd_start` vs `on_style_chosen` |
| n7 | Bot | No `__all__` exports in any bot module |
| n8 | Bot | `credits` module import aliased to `credits_handler` to avoid builtin shadow — consider renaming module |
| n9 | AI | No timeout or retry contract defined in abstract interface |
| n10 | AI | Anthropic client instantiated per-service, not shared — no connection pooling between tasks |
| n11 | Storage | No `Content-Disposition` header on uploaded files — browser displays instead of downloads |
| n12 | Payments | `verify_webhook` returns only `bool` — real implementation needs parsed payment data |
| n13 | Config | `AVAILABLE_STYLES` is mutable list — should be tuple or frozenset |
| n14 | Config | `CREDIT_PACKS` type `list[dict[str, int]]` — consider NamedTuple or dataclass |
| n15 | API | `AsyncGenerator[None]` lifespan type hint could be `AsyncIterator[None]` |
| n16 | API | `noqa: B008` on `Depends()` could use per-file-ignores in ruff config instead |
| n17 | API | `uvicorn.run(reload=True)` hardcoded in `__main__` block |
| n18 | Docker | `Dockerfile.worker` does not copy `alembic/` — intentional but undocumented |
| n19 | Makefile | `up-all`, `downgrade`, `test-cov` missing from `.PHONY` |
| n20 | Makefile | `revision` target accepts empty `MSG` without validation |

---

## Top 5 Recommendations (Priority Order)

1. **Fix credit lifecycle** — Add `refund_credits()` service function; call it on generation failure; make charge + dispatch atomic (or use transactional outbox).

2. **Fix session management** — Add commit/rollback to `get_async_session`; add rollback in `AuthMiddleware` catch block; remove bottom-of-file circular imports.

3. **Cache `get_settings()`** — Add `@lru_cache`; refactor `db/session.py` to use lazy engine creation instead of module-level instantiation.

4. **Harden Celery task** — Re-raise exceptions (don't swallow); add `self.retry()` for transient failures; check Telegram API responses; enforce slide count limit.

5. **Security hardening** — Use `hmac.compare_digest()` for all secrets; validate defaults aren't shipped to prod; add non-root Docker user; bind dev ports to localhost.

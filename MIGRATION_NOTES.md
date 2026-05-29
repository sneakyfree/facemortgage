# Migration Notes (2026-05-24)

## Known issue: alembic migration tree is forked

`backend/alembic/versions/` has two root migrations:

- `000_sqlite` — a SQLite-compatible whole-schema baseline.
- `001_initial_schema` through `015_add_password_reset` — Postgres-only chain that uses raw `CREATE TYPE`, `UUID`, etc.

They are reunited by the merge revision `ce8febf2a634_merge_heads`. As a result, `alembic upgrade head` from a clean Postgres DB traverses BOTH branches and fails with `DuplicateObjectError` or `DuplicateTableError`. Worse, `000_sqlite` is incomplete: it omits `users.is_super_admin` added in migration 008, so even if you stamp it and skip the postgres chain you get runtime errors when the User model is queried.

## Workaround for fresh dev DB

Bypass the migration tree and build the schema directly from the SQLAlchemy models:

```
cd backend
docker exec facemortgage-pg psql -U facemortgage -d facemortgage \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; \
      GRANT ALL ON SCHEMA public TO facemortgage;"
DATABASE_URL=postgresql+asyncpg://facemortgage:facemortgage_dev@localhost:5491/facemortgage \
  scripts/bootstrap-dev-schema.sh
```

That script calls `Base.metadata.create_all` (the same path the pytest fixture uses, after the conftest patch below) and then `alembic stamp head` so future migrations can layer on top.

## Permanent fix (TODO before adding new migrations)

Collapse the fork by either:

1. **Delete `000_sqlite` entirely** and have everyone target Postgres. Strip the SQLite-only branch label from later migrations.
2. **Make `000_sqlite` the canonical schema** (including `is_super_admin` and every other column added through 015), then point `001`'s `down_revision` at `000_sqlite` and strip the `CREATE TYPE` ops that would now collide. This is more work but preserves the SQLite-baseline path.

Either approach is mechanical — schedule it before adding migration 016.

## Adjacent fixes already applied 2026-05-24

- `alembic/versions/005_add_scheduled_calls_and_soft_leads.py`
  - The explicit `postgresql.ENUM.create(...)` for `scheduledcallstatus` and `softleadstatus` raced the column-level `sa.Enum` types. Now uses idempotent `DO $$ ... EXCEPTION WHEN duplicate_object ... END $$` blocks, and the column-level types reuse the pre-declared variables (or set `create_type=False`).
  - `op.create_index` calls that duplicated `index=True` from column declarations were removed (`ix_scheduled_calls_scheduled_for`, `ix_soft_leads_email`, `ix_soft_leads_created_at`).

- `backend/tests/conftest.py` now honors a `TEST_DATABASE_URL` env var. Pointing it at Postgres unblocks all the model-test errors (`UUID` cannot be compiled for SQLite). With `TEST_DATABASE_URL=postgresql+asyncpg://facemortgage:facemortgage_dev@localhost:5491/facemortgage_test` the suite goes from 378/560 to 560/560.

- `backend/src/app/core/cache.py` referenced `settings.REDIS_URL` (uppercase); pydantic-settings exposes `redis_url`. Fixed — `/api/v1/health/ready` now reports redis healthy.

- `backend/src/app/api/v1/router.py` was including the `health` router with `prefix="/health"` on top of routes that already started with `/health/...`, yielding `/api/v1/health/health/ready`. Same shape in `thumbnails` (router-level prefix + include prefix). The external `prefix` is removed from `router.py` for health; the internal `prefix` is removed from `thumbnails.py`.

- `backend/src/app/core/database.py` now exposes a `get_async_engine()` accessor; the performance middleware was importing a function name that didn't exist and crashing `/api/v1/performance/` with `ImportError`.

- `backend/src/app/api/v1/routes/auth.py` `resend_verification_email` passed `template_data=...` to `EmailService.send_email`, which expects `context=...`. Fixed both call sites (lines 333 and ~415).

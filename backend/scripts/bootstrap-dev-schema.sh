#!/usr/bin/env bash
# Bootstrap the dev database schema directly from the SQLAlchemy models,
# bypassing the forked alembic migration tree (000_sqlite is a parallel
# branch that lacks columns added in 008+). Use this for fresh dev DBs
# until the migration tree is collapsed into a single chain.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# DATABASE_URL must point at a clean Postgres instance.
: "${DATABASE_URL:?DATABASE_URL must be set, e.g. postgresql+asyncpg://facemortgage:facemortgage_dev@localhost:5491/facemortgage}"

PYTHONPATH=. venv/bin/python -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from src.app.core.database import Base
import src.app.models  # registers all model classes
async def main():
    e = create_async_engine(os.environ[DATABASE_URL], echo=False)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await e.dispose()
    print(schema created from models)
asyncio.run(main())
"

# Mark alembic at the merge head so any new migrations layer on top.
venv/bin/alembic stamp head

import logging
import time
from contextvars import ContextVar
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.app.config import settings

logger = logging.getLogger("sqlalchemy.slow_queries")

# Context variable to store query start time
_query_start_time: ContextVar[float] = ContextVar("query_start_time", default=0.0)

# Slow query threshold in seconds (queries taking longer than this are logged)
SLOW_QUERY_THRESHOLD = getattr(settings, "slow_query_threshold", 0.5)


class Base(DeclarativeBase):
    pass


# Check if using SQLite (doesn't support pool_size/max_overflow)
is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.debug,
    )


# Slow query logging using SQLAlchemy events
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    _query_start_time.set(time.time())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries."""
    start_time = _query_start_time.get()
    if start_time:
        elapsed = time.time() - start_time
        if elapsed > SLOW_QUERY_THRESHOLD:
            # Truncate very long queries for logging
            truncated_stmt = statement[:500] + "..." if len(statement) > 500 else statement
            logger.warning(
                f"Slow query ({elapsed:.3f}s): {truncated_stmt}",
                extra={
                    "duration_seconds": elapsed,
                    "statement_preview": truncated_stmt,
                    "executemany": executemany,
                },
            )

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

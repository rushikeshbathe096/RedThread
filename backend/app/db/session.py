import uuid
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("redthread.db")

# Asynchronous SQLAlchemy 2.0 Engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DEBUG,
    future=True,
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def set_session_tenant_context(
    session: AsyncSession,
    org_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    is_worker: bool = False,
) -> None:
    """Sets PostgreSQL transaction-local session variables for Row-Level Security (RLS)."""
    org_str = str(org_id) if org_id else ""
    user_str = str(user_id) if user_id else ""
    worker_str = "true" if is_worker else "false"

    await session.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"),
        {"org_id": org_str},
    )
    await session.execute(
        text("SELECT set_config('app.current_user_id', :user_id, true)"),
        {"user_id": user_str},
    )
    await session.execute(
        text("SELECT set_config('app.is_worker', :is_worker, true)"),
        {"is_worker": worker_str},
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding transactional database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session rolled back due to error", error=str(e))
            raise
        finally:
            await session.close()

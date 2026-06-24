"""
Database session dependencies.

Provides async session dependencies for route handlers.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.core.config import settings
from apps.api.core.database import engine

logger = logging.getLogger(__name__)


# ===============================
# SESSION FACTORY
# ===============================


def create_database_engine() -> create_async_engine:
    """
    Create async database engine.

    Returns:
        Async database engine
    """
    logger.info(f"Creating async database engine for {settings.DATABASE_URL.split('://')[0]}")

    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=settings.DATABASE_POOL_PREPARE,
    )


async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session from pool.

    Yields:
        AsyncSession: Database session

    Raises:
        Exception: If session creation fails
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            logger.error(f"Database session error: {exc}")
            await session.rollback()
            raise


# ===============================
# ENGINE
# ===============================

engine = create_database_engine()

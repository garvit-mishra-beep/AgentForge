"""
Database configuration and session management.

Async SQLAlchemy setup with connection pooling and session factory.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from apps.api.core.config import settings

logger = logging.getLogger(__name__)


# ===============================
# ENGINE FACTORY
# ===============================


def create_database_engine() -> create_async_engine:
    """
    Create async database engine with pooling.

    Returns:
        Async database engine with pool settings
    """
    logger.info(f"Creating async database engine for {settings.DATABASE_URL.split('://')[0]}")

    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=settings.DATABASE_POOL_PREPARE,
        echo=settings.ENVIRONMENT == "development",
    )

    return engine


# ===============================
# SESSION FACTORY
# ===============================


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Yields:
        AsyncSession: Database session

    Raises:
        Exception: If session creation fails
    """
    engine = create_database_engine()
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        try:
            yield session
        except Exception as exc:
            logger.error(f"Database session error: {exc}")
            await session.rollback()
            raise
        finally:
            await session.commit()


def has_vector_extension() -> bool:
    """Check if pgvector extension is enabled/active."""
    from packages.state.models import workflow_execution
    return getattr(workflow_execution, "_has_vector_extension", False)


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables from declarative base.
    """
    from packages.state.models.base import Base
    # Import all models to register them on Base.metadata
    from packages.state.models.user import User, Role, UserRole, Permission, UserPermission
    from packages.state.models.workflow import Workflow, Execution, Task, EventLog
    from packages.state.models.workflow_execution import (
        ExecutionState,
        Checkpoint,
        Actor,
        ActorExecution,
        Message,
        Output,
        Metric,
        ProjectMemory,
    )
    from packages.state.models import workflow_execution
    from sqlalchemy import text

    engine = create_database_engine()

    # 1. Try to create the vector extension before creating tables
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        workflow_execution._has_vector_extension = True
        logger.info("Successfully enabled pgvector extension in database")
    except Exception as e:
        workflow_execution._has_vector_extension = False
        logger.warning(f"pgvector extension is not available (falling back to JSON/Text): {e}")

    # 2. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # 3. Ensure columns exist dynamically
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE project_memories ADD COLUMN IF NOT EXISTS embedding_data TEXT"))
        logger.info("Ensured embedding_data column exists in project_memories table")
    except Exception as e:
        logger.warning(f"Skipped dynamically adding embedding_data column: {e}")

    try:
        async with engine.begin() as conn:
            if getattr(workflow_execution, "_has_vector_extension", False):
                await conn.execute(text("ALTER TABLE project_memories ADD COLUMN IF NOT EXISTS embedding vector(768)"))
            else:
                await conn.execute(text("ALTER TABLE project_memories ADD COLUMN IF NOT EXISTS embedding TEXT"))
        logger.info("Ensured embedding column exists in project_memories table")
    except Exception as e:
        logger.warning(f"Skipped dynamically adding embedding column: {e}")



# ===============================
# DEclarative Base
# ===============================


class AsyncBase(MappedAsDataclass, DeclarativeBase):
    """
    SQLAlchemy async declarative base.

    All models should inherit from this class.
    """

    pass


# ===============================
# ENGINE INSTANCE
# ===============================

engine = create_database_engine()
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

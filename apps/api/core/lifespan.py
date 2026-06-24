"""
FastAPI lifespan manager hooks.

Startup and shutdown lifecycle management for AgentOS API.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator

from apps.api.core.config import settings
from apps.api.core.database import engine, init_db
from apps.api.core.redis import close_redis

logger = logging.getLogger(__name__)


# ===============================
# STARTUP TASKS
# ===============================


async def startup_task_database() -> None:
    """
    Run database initialization on startup.
    """
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def startup_task_redis() -> None:
    """
    Verify Redis connectivity on startup.
    """
    try:
        from apps.api.core.redis import redis_pool
        await redis_pool.ping()
        logger.info("Redis connectivity verified")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        # Don't raise - Redis might be optional


async def startup_task_websocket() -> None:
    """
    Initialize websocket manager on startup.
    """
    try:
        from apps.api.websocket.manager import websocket_manager
        await websocket_manager.start()
        logger.info("Websocket manager started")
    except Exception as e:
        logger.error(f"Websocket manager startup failed: {e}")
        raise


# ===============================
# SHUTDOWN TASKS
# ===============================


async def shutdown_task_redis() -> None:
    """
    Close Redis connection on shutdown.
    """
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis: {e}")


async def shutdown_task_metrics() -> None:
    """
    Flush metrics on shutdown.
    """
    try:
        if settings.ENABLE_METRICS:
            from apps.api.observability.metrics import flush_metrics
            await flush_metrics()
            logger.info("Metrics flushed")
    except Exception as e:
        logger.warning(f"Error flushing metrics: {e}")


# ===============================
# LIFESPAN GENERATOR
# ===============================


async def lifespan_manager(
    receive: Any,
    send: Any,
) -> AsyncGenerator[Any, None]:
    """
    FastAPI lifespan generator for startup/shutdown hooks.

    Args:
        receive: ASGI receive channel
        send: ASGI send channel

    Yields:
        None

    Raises:
        Exception: On startup failure
    """
    # Startup hooks
    logger.info("Application starting up")

    # Run startup tasks
    startup_tasks = [
        ("database", startup_task_database),
        ("redis", startup_task_redis),
    ]

    if settings.ENVIRONMENT == "development":
        # Add websocket to startup in dev
        startup_tasks.append(("websocket", startup_task_websocket))

    try:
        # Run tasks concurrently if async
        if asyncio.iscoroutinefunction(startup_task_database):
            await asyncio.gather(
                startup_task_database(),
                startup_task_redis(),
            )
        else:
            startup_task_database()
            startup_task_redis()

        logger.info("Startup completed")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown hooks
    logger.info("Application shutting down")

    # Run shutdown tasks
    shutdown_tasks = [
        ("redis", shutdown_task_redis),
        ("metrics", shutdown_task_metrics),
    ]

    try:
        for name, task in shutdown_tasks:
            await task()

        logger.info("Shutdown completed")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")
        # Don't raise on shutdown errors - just log


# ===============================
# SYNC WRAPPER (for plain FastAPI)
# ===============================


def create_lifespan_context(
    receive: Any,
    send: Any,
) -> AsyncGenerator[Any, None]:
    """
    Create lifespan context generator.

    Args:
        receive: ASGI receive channel
        send: ASGI send channel

    Returns:
        Async generator for lifespan
    """
    return lifespan_manager(receive, send)

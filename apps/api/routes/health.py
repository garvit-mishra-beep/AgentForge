"""
Health check routes.

Liveness and readiness endpoints for AgentOS API.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis

from apps.api.core.config import settings
from apps.api.core.database import engine

logger = logging.getLogger(__name__)

router = APIRouter()


# ===============================
# HEALTH ENDPOINTS
# ===============================


@router.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Basic health check endpoint for liveness",
)
async def health_check(request: Request):
    """
    Health check endpoint.

    Returns:
        Health status information
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.APPLICATION_NAME,
    }

    logger.info("Health check", request_id=request.headers.get("x-correlation-id", "unknown"))

    return JSONResponse(status_code=200, content=health_data)


@router.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness check",
    description="Checks if application is ready to serve traffic",
)
async def readiness_check(request: Request):
    """
    Readiness health check.

    Checks database and Redis connectivity.

    Returns:
        Readiness status
    """
    ready = True
    errors = []

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception as e:
        ready = False
        errors.append(f"Database connection failed: {e}")
        logger.error(f"Database health check failed: {e}")

    # Check Redis
    try:
        redis_pool = await redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_DB,
        )
        await redis_pool.ping()
        await redis_pool.close()
    except Exception as e:
        ready = False
        errors.append(f"Redis connection failed: {e}")
        logger.error(f"Redis health check failed: {e}")

    if ready:
        logger.info("Readiness check passed")
    else:
        logger.warning(
            "Readiness check failed",
            errors=errors,
            request_id=request.headers.get("x-correlation-id", "unknown"),
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready" if ready else "unhealthy",
            "errors": errors if not ready else None,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness check",
    description="Quick liveness check for load balancers",
)
async def liveness_check(request: Request):
    """
    Liveness check endpoint.

    Fast response for load balancer health checks.

    Returns:
        Liveness status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

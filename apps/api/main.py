"""
AgentOS API Gateway - Production FastAPI Application.

Async-first, horizontally scalable backend for multi-agent orchestration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from sqlalchemy import select

from apps.api.core.config import settings
from apps.api.core.logging import bootstrap_logging
from apps.api.core.database import engine
from apps.api.core.redis import redis_pool
from apps.api.middleware.logging_middleware import LoggingMiddleware
from apps.api.middleware.error_handler import register_exception_handlers
from apps.api.middleware.request_context import RequestContextMiddleware
from apps.api.routes.health import router as health_router
from apps.api.routes.auth import router as auth_router
from apps.api.routes.workflows import router as workflow_router
from apps.api.routes.websocket import router as websocket_router
from apps.api.routes.settings import router as settings_router
from apps.api.websocket.manager import websocket_manager


# ===============================
# LOGGING BOOTSTRAP
# ===============================

logger = logging.getLogger(__name__)
bootstrap_logging(logger)

# ===============================
# APPLICATION LIFESPAN MANAGER
# ===============================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Startup:
    - Initialize database connection pool
    - Connect to Redis
    - Initialize logging
    - Create websocket manager

    Shutdown:
    - Close Redis connection
    - Engine disposal
    """
    # Startup
    logger.info("AgentOS API Gateway starting up")

    # Verify database connection
    async with engine.connect() as conn:
        await conn.execute(select(1))
    logger.info("Database connection established")

    # Initialize database tables
    from apps.api.core.database import init_db
    try:
        await init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database table initialization failed: {e}")

    # Verify Redis connection (optional - app works without Redis for websockets)
    try:
        await redis_pool.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed (continuing without Redis): {e}")

    # Initialize websocket manager
    await websocket_manager.start()
    logger.info("Websocket manager started")

    yield

    # Shutdown
    logger.info("Shutting down AgentOS API Gateway")
    try:
        await redis_pool.close()
    except Exception as e:
        logger.warning(f"Error closing Redis: {e}")
    await engine.dispose()
    await websocket_manager.shutdown()


# ===============================
# APPLICATION FACTORY
# ===============================

app = FastAPI(
    title="AgentOS API Gateway",
    description="Production-grade async FastAPI backend for multi-agent orchestration",
    version=settings.ENVIRONMENT,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# ===============================
# MIDDLEWARE REGISTRATION
# ===============================

# CORS middleware - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request context middleware for correlation IDs
app.add_middleware(RequestContextMiddleware)

# Logging middleware for request timing
app.add_middleware(LoggingMiddleware)

# ===============================
# EXCEPTION HANDLERS
# ===============================

register_exception_handlers(app)

# ===============================
# ROUTE MOUNTING
# ===============================

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(workflow_router, prefix="/api", tags=["Workflows"])
app.include_router(websocket_router, prefix="/api", tags=["WebSockets"])
app.include_router(settings_router, prefix="/api", tags=["Settings"])

# ===============================
# ROOT ENDPOINT
# ===============================

@app.get("/")
async def root():
    """
    API gateway root endpoint.
    """
    return {
        "service": "AgentOS API Gateway",
        "version": settings.ENVIRONMENT,
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None
    }


# ===============================
# CUSTOM 404 HANDLER
# ===============================


@app.exception_handler(404)
async def custom_404_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": str(exc)}
    )


# ===============================
# FACTORY FUNCTION
# ===============================


def create_app() -> FastAPI:
    """
    Application factory function.

    Returns:
        FastAPI application instance
    """
    return app


# ===============================
# ENTRY POINT
# ===============================

if __name__ == "__main__":
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )

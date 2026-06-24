from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from apps.api.core.config import settings
from apps.api.core.logging import bootstrap_logging
from apps.api.core.database import init_db, engine
from apps.api.core.exceptions import register_exception_handlers
from apps.api.core.telemetry import setup_telemetry
from apps.api.core.health import health_checker
from apps.api.core.metrics import track_request, metrics_endpoint
from apps.api.middleware.logging import LoggingMiddleware
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.middleware.audit import AuditMiddleware
from apps.api.routes import auth_router, agents_router, workflows_router, executions_router, observability_router, ws_router, rag_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_logging()
    logger.info(f"Starting {settings.APPLICATION_NAME} (env={settings.ENVIRONMENT})")
    await init_db()
    setup_telemetry(app, db_engine=engine)
    logger.info("Application started")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APPLICATION_NAME,
    description="Build, Deploy, Monitor, and Scale AI Agents from a Single Platform",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)
register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(observability_router, prefix="/api/v1")
app.include_router(ws_router)
app.include_router(rag_router, prefix="/api/v1")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    track_request(method=request.method, path=request.url.path, status=response.status_code, duration=duration)
    return response


@app.get("/api/v1/health")
async def health():
    return await health_checker.run_all()


@app.get("/api/v1/ready")
async def ready():
    return await health_checker.run_critical()


@app.get("/api/v1/live")
async def live():
    return await health_checker.liveness()


@app.get("/metrics")
async def metrics():
    return Response(content=metrics_endpoint(), media_type="text/plain")


@app.get("/")
async def root():
    return {"service": settings.APPLICATION_NAME, "docs": "/docs", "api": "/api/v1"}


def create_app() -> FastAPI:
    return app

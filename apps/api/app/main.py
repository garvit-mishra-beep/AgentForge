import sys

sys.modules["langchain"] = None  # type: ignore

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.auth import auth_middleware
from app.routes.analytics import router as analytics_router
from app.routes.auth import router as auth_router
from app.routes.context import router as context_router
from app.routes.executions import router as executions_router
from app.routes.feedback import router as feedback_router
from app.routes.github import router as github_router
from app.routes.health import router as health_router
from app.routes.keys import router as keys_router
from app.routes.memories import router as memories_router
from app.routes.projects import router as projects_router
from app.routes.review import router as review_router
from app.routes.review import start_worker, stop_worker
from app.routes.tasks import router as tasks_router
from app.routes.teams import router as teams_router
from core.config import settings
from core.database import DatabasePool
from core.logging_config import setup_logging
from core.observability import (
    emit,
    generate_correlation_id,
    get_request_metrics,
    record_request_metric,
)
from core.redis import close_redis, init_redis, rate_limit_check
from core.task_tracker import tracker

setup_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)

_SKIP_RATE_LIMIT_ROUTES = {
    "GET:/api/v1/health",
    "GET:/docs",
    "GET:/openapi.json",
    "GET:/redoc",
}

_AUTH_RATE_LIMIT_ROUTES = {
    "POST:/api/v1/auth/login",
    "POST:/api/v1/auth/register",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate()

    pool = DatabasePool()
    await pool.initialize()
    await pool.run_migrations()
    app.state.db = pool

    await init_redis()
    start_worker()

    logger.info(
        "AgentForge API started (auth=%s, fast_demo=%s, log_format=%s)",
        settings.auth_enabled, settings.fast_demo_mode, settings.log_format,
    )

    yield

    logger.info("Shutting down AgentForge API...")
    stop_worker()
    await tracker.shutdown(timeout=30.0)
    await close_redis()
    await pool.close()
    logger.info("AgentForge API stopped")


_GLOBAL_RL_PREFIX = "global_ratelimit:"


async def rate_limit_middleware(request, call_next):
    path = request.url.path
    method = request.method
    if method == "OPTIONS":
        return await call_next(request)
    route_key = f"{method}:{path}"

    if route_key in _SKIP_RATE_LIMIT_ROUTES:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    if route_key in _AUTH_RATE_LIMIT_ROUTES:
        limit = settings.rate_limit_auth_per_minute
    else:
        limit = settings.rate_limit_per_minute

    allowed = await rate_limit_check(client_ip, limit=limit, window=60, key_prefix=_GLOBAL_RL_PREFIX)
    if not allowed:
        emit("rate_limit_hit", {"ip": client_ip, "route": route_key, "limit": limit})
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
            headers={"Retry-After": "60"},
        )

    return await call_next(request)


async def correlation_middleware(request, call_next):
    cid = request.headers.get("x-correlation-id", generate_correlation_id())
    request.state.correlation_id = cid
    start = time.monotonic()

    response = await call_next(request)

    duration_ms = (time.monotonic() - start) * 1000
    response.headers["X-Correlation-ID"] = cid

    record_request_metric(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        correlation_id=cid,
    )

    return response


def _prometheus_metrics():
    lines = [
        '# HELP agentforge_requests_total Total request count',
        '# TYPE agentforge_requests_total counter',
    ]
    metrics = get_request_metrics()
    by_status: dict[int, int] = {}
    total_duration = 0.0
    for m in metrics:
        by_status[m.status_code] = by_status.get(m.status_code, 0) + 1
        total_duration += m.duration_ms

    for status, count in sorted(by_status.items()):
        lines.append(f'agentforge_requests_total{{status="{status}"}} {count}')

    lines.append('')
    lines.append('# HELP agentforge_request_duration_ms Request duration in ms')
    lines.append('# TYPE agentforge_request_duration_ms gauge')
    if metrics:
        avg = total_duration / len(metrics)
        lines.append(f'agentforge_request_duration_ms{{quantile="avg"}} {round(avg, 2)}')
    lines.append(f'agentforge_request_duration_ms{{quantile="count"}} {len(metrics)}')

    lines.append('')
    lines.append('# HELP agentforge_active_background_tasks Current background task count')
    lines.append('# TYPE agentforge_active_background_tasks gauge')
    lines.append(f'agentforge_active_background_tasks {tracker.active_count}')

    return PlainTextResponse('\n'.join(lines) + '\n')


async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    return response


app = FastAPI(
    title="AgentForge API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(correlation_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(auth_middleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(keys_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(context_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(memories_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1")


@app.get("/api/v1/metrics")
async def metrics():
    return _prometheus_metrics()

# Trigger hot-reload to load updated Google OAuth credentials from .env


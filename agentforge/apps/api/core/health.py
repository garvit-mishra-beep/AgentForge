from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from apps.api.core.config import settings

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    def __init__(self):
        self._checks: dict[str, Any] = {}
        self._started_at = datetime.now(timezone.utc)

    def register(self, name: str, check_func, critical: bool = True) -> None:
        self._checks[name] = {"func": check_func, "critical": critical}

    async def run_all(self) -> dict:
        results = {}
        overall = HealthStatus.HEALTHY
        for name, cfg in self._checks.items():
            try:
                ok = await cfg["func"]()
                results[name] = {"status": "ok" if ok else "error"}
                if not ok:
                    if cfg["critical"]:
                        overall = HealthStatus.UNHEALTHY
                    elif overall != HealthStatus.UNHEALTHY:
                        overall = HealthStatus.DEGRADED
            except Exception as e:
                results[name] = {"status": "error", "detail": str(e)}
                if cfg["critical"]:
                    overall = HealthStatus.UNHEALTHY
                elif overall != HealthStatus.UNHEALTHY:
                    overall = HealthStatus.DEGRADED
        return {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.ENVIRONMENT,
            "version": "0.1.0",
            "uptime_seconds": int((datetime.now(timezone.utc) - self._started_at).total_seconds()),
            "checks": results,
        }

    async def run_critical(self) -> dict:
        results = {}
        overall = HealthStatus.HEALTHY
        for name, cfg in self._checks.items():
            if not cfg["critical"]:
                continue
            try:
                ok = await cfg["func"]()
                results[name] = {"status": "ok" if ok else "error"}
                if not ok:
                    overall = HealthStatus.UNHEALTHY
            except Exception as e:
                results[name] = {"status": "error", "detail": str(e)}
                overall = HealthStatus.UNHEALTHY
        return {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": results,
        }

    async def liveness(self) -> dict:
        return {
            "status": HealthStatus.HEALTHY,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int((datetime.now(timezone.utc) - self._started_at).total_seconds()),
        }


health_checker = HealthCheck()


async def check_database() -> bool:
    try:
        from apps.api.core.database import async_session
        async with async_session() as session:
            await session.execute(__import__("sqlalchemy").text("SELECT 1"))
            return True
    except Exception as e:
        logger.warning("Database health check failed: %s", e)
        return False


async def check_redis() -> bool:
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        await r.ping()
        await r.aclose()
        return True
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)
        return False


async def check_qdrant() -> bool:
    try:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        await client.get_collections()
        await client.close()
        return True
    except Exception as e:
        logger.warning("Qdrant health check failed: %s", e)
        return False


health_checker.register("database", check_database, critical=True)
health_checker.register("redis", check_redis, critical=False)
health_checker.register("qdrant", check_qdrant, critical=False)

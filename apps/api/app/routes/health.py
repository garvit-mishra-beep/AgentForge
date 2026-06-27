from datetime import UTC, datetime

from fastapi import APIRouter

from core.config import settings
from core.observability import get_health_metrics

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "auth_enabled": settings.auth_enabled,
        "fast_demo_mode": settings.fast_demo_mode,
        "metrics": get_health_metrics(),
    }

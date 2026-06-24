from __future__ import annotations

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

RATE_LIMITED_PATHS = {
    "/api/v1/auth/token": (settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_PERIOD),
    "/api/v1/auth/register": (10, 3600),
    "/api/v1/rag/upload": (20, 60),
}


class RateLimitStore:
    def __init__(self):
        self._store: dict[str, list[float]] = {}

    def check(self, key: str, max_requests: int, window: int) -> bool:
        now = time.time()
        timestamps = self._store.get(key, [])
        timestamps = [t for t in timestamps if now - t < window]
        self._store[key] = timestamps
        if len(timestamps) >= max_requests:
            return False
        timestamps.append(now)
        return True


_store = RateLimitStore()


def rate_limit_key(request: Request) -> str:
    client = request.client.host if request.client else "unknown"
    route = request.url.path
    return f"rl:{client}:{route}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, store: RateLimitStore | None = None):
        super().__init__(app)
        self.store = store or _store

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        client_host = request.client.host if request.client else None
        limits = RATE_LIMITED_PATHS.get(path)
        if limits:
            key = f"rl:{client_host}:{path}"
            max_r, window = limits
            if not self.store.check(key, max_r, window):
                logger.warning(f"Rate limit exceeded for {key}")
                raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
        return await call_next(request)

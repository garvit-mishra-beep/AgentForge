from __future__ import annotations

import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apps.api.services.audit import AuditService
from apps.api.core.database import async_session

logger = logging.getLogger(__name__)

AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

AUDIT_RESOURCE_MAP = {
    "/api/v1/agents": "agent",
    "/api/v1/workflows": "workflow",
    "/api/v1/executions": "execution",
    "/api/v1/auth/token": "auth",
    "/api/v1/auth/register": "auth",
    "/api/v1/rag": "rag_document",
    "/api/v1/observability": "observability",
}


def _extract_resource(path: str) -> str:
    for prefix, resource in AUDIT_RESOURCE_MAP.items():
        if path.startswith(prefix):
            return resource
    return "unknown"


def _parse_actor(request: Request) -> uuid.UUID | None:
    try:
        user = getattr(request.state, "user", None)
        if user and isinstance(user, dict):
            sub = user.get("sub")
            if sub:
                return uuid.UUID(sub) if isinstance(sub, str) and len(sub) > 30 else None
    except Exception:
        pass
    return None


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method
        client_host = request.client.host if request.client else None
        response = await call_next(request)
        if method in AUDIT_METHODS and response.status_code < 500:
            resource_type = _extract_resource(path)
            if resource_type != "unknown":
                try:
                    actor_id = _parse_actor(request)
                    async with async_session() as db:
                        svc = AuditService(db)
                        await svc.log(
                            actor_id=actor_id,
                            tenant_id=getattr(request.state, "tenant_id", None),
                            action=f"{method.lower()}.{resource_type}",
                            resource_type=resource_type,
                            meta_data={"path": path, "status": response.status_code},
                            ip_address=client_host,
                        )
                        await db.commit()
                except Exception as e:
                    logger.warning(f"Audit log failed: {e}")
        return response

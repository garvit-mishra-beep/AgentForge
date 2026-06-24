"""
Request context middleware.

Generates and stores request context data (correlation IDs, etc.).
"""

import secrets
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from apps.api.core.logging import get_structlog_logger
logger = get_structlog_logger(__name__)


# ===============================
# REQUEST CONTEXT
# ===============================


class RequestContext:
    """
    Request context data storage.

    Stores correlation IDs and other request-scoped data.
    """

    def __init__(self, request_id: str | None = None):
        """
        Initialize request context.

        Args:
            request_id: Optional request ID
        """
        self.request_id = request_id or self._generate_request_id()
        self.start_time: float | None = None
        self.endpoint: str | None = None
        self.user_id: str | None = None
        self.tags: dict = {}

    def _generate_request_id(self) -> str:
        """Generate request ID."""
        return f"{self.__class__.__name__}:{uuid.uuid4().hex[:8]}"

    def set_endpoint(self, endpoint: str) -> None:
        """Set endpoint name."""
        self.endpoint = endpoint

    def set_user_id(self, user_id: str | None) -> None:
        """Set user ID from auth."""
        self.user_id = user_id

    def set_tags(self, **tags: Any) -> None:
        """Set request tags."""
        self.tags.update(tags)

    def to_dict(self) -> dict:
        """
        Get context as dictionary.

        Returns:
            Request context dict
        """
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "user_id": self.user_id,
            "tags": self.tags,
        }


# ===============================
# MIDDLEWARE
# ===============================


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set request context.

    Generates correlation IDs and stores request metadata.
    """

    def __init__(self, app):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Any:
        """
        Handle incoming request.

        Args:
            request: Request object
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Generate or extract correlation ID
        request_id = request.headers.get("x-correlation-id")

        if request_id is None:
            # Generate new correlation ID
            request_id = secrets.token_hex(8)
            headers = list(request.scope["headers"])
            headers.append((b"x-correlation-id", request_id.encode("latin-1")))
            request.scope["headers"] = headers

        # Create request context
        context = RequestContext(request_id=request_id)

        # Wrap response for context attachment
        async def response_modifier(response: Any):
            # Attach context headers to response
            response.headers["x-correlation-id"] = request_id
            response.headers["x-request-id"] = request_id

            # Store context for later use
            request.context = context

            return response

        # Set request start time
        context.start_time = time.perf_counter()

        try:
            # Process request through next middleware
            response = await call_next(request)

            # Log request completion
            logger.info(
                "Request started",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=(time.perf_counter() - context.start_time) * 1000
                if context.start_time
                else 0,
            )

            return response

        except Exception as exc:
            # Log exception with context
            logger.exception(
                "Request error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                exc_info=str(exc),
            )
            raise

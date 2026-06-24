"""
Request logging middleware.

Logs request/response timing and status codes.
"""

import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from apps.api.core.logging import get_structlog_logger
logger = get_structlog_logger(__name__)
from apps.api.core.config import settings


# ===============================
# MIDDLEWARE
# ===============================


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logging middleware for request metrics.

    Logs request start/end, duration, and response status.
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
        Handle request logging.

        Args:
            request: Request object
            call_next: Next middleware/handler

        Returns:
            Response
        """
        request_start_time = time.perf_counter()

        # Get method and path
        method = request.method
        path = request.url.path

        try:
            # Process request
            response = await call_next(request)

        except Exception as exc:
            # Log exception
            logger.exception(
                "Request error",
                path=path,
                method=method,
                exc_info=type(exc).__name__,
            )
            raise

        # Log response
        status_code = response.status_code
        duration = (time.perf_counter() - request_start_time) * 1000

        logger.info(
            "Request completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration, 2),
            request_id=request.headers.get("x-correlation-id", "unknown"),
            response_size=response.headers.get("content-length", 0),
        )

        return response


# ===============================
# WEBSOCKET LOGGING
# ===============================


class WebSocketLoggingMiddleware:
    """
    Middleware for logging websocket events.

    Logs connection, disconnect, and message counts.
    """

    def __init__(self, app, interval=10):
        """
        Initialize websocket logging.

        Args:
            app: WebSocket application
            interval: Heartbeat interval in seconds
        """
        self.app = app
        self.interval = interval

    async def on_connect(self, websocket, subprotocol=None):
        """
        Log websocket connection.

        Args:
            websocket: WebSocket connection
            subprotocol: Subprotocol if any
        """
        logger.info(
            "Websocket connected",
            path=websocket.path,
            subprotocol=subprotocol or "none",
            request_id=websocket.request.headers.get(
                "x-correlation-id", "unknown"
            ),
        )

    async def on_disconnect(self, websocket, close_code=None):
        """
        Log websocket disconnection.

        Args:
            websocket: WebSocket connection
            close_code: Close code
        """
        logger.info(
            "Websocket disconnected",
            path=websocket.path,
            close_code=close_code,
            request_id=websocket.request.headers.get(
                "x-correlation-id", "unknown"
            ),
        )

    async def on_receive(self, websocket, message, subprotocol=None):
        """
        Log websocket message receipt.

        Args:
            websocket: WebSocket connection
            message: Received message
            subprotocol: Subprotocol if any
        """
        logger.debug(
            "Websocket message received",
            path=websocket.path,
            message_size=len(message),
            subprotocol=subprotocol or "none",
            request_id=websocket.request.headers.get(
                "x-correlation-id", "unknown"
            ),
        )

    async def on_send(self, websocket, message, subprotocol=None):
        """
        Log websocket message send.

        Args:
            websocket: WebSocket connection
            message: Sent message
            subprotocol: Subprotocol if any
        """
        logger.debug(
            "Websocket message sent",
            path=websocket.path,
            message_size=len(message),
            subprotocol=subprotocol or "none",
            request_id=websocket.request.headers.get(
                "x-correlation-id", "unknown"
            ),
        )

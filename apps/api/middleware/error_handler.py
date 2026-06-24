"""
Centralized exception handler registration.

Registers global exception handlers with FastAPI.
"""

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.api.core.config import settings
from apps.api.core.exceptions import (
    exception_handler_exception,
    exception_handler_internal_error,
    exception_handler_pydantic_error,
    exception_handler_validation_error,
)

logger = logging.getLogger(__name__)


# ===============================
# REGISTRATION
# ===============================


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers globally.

    Args:
        app: FastAPI application instance

    Returns:
        None
    """
    # Register exception handlers
    app.add_exception_handler(
        StarletteHTTPException,
        exception_handler_exception,
    )
    app.add_exception_handler(
        RequestValidationError,
        exception_handler_validation_error,
    )
    app.add_exception_handler(
        Exception,
        exception_handler_internal_error,
    )

    # Also handle 404s
    from fastapi.routing import APIRoute
    app.add_exception_handler(
        HTTPException,
        exception_handler_exception,
    )

    logger.info(f"Exception handlers registered for {settings.APPLICATION_NAME}")


# ===============================
# REQUEST ID MIDDLEWARE
# ===============================


async def add_request_id_middleware(app, call_next, request):
    """
    Middleware to add request ID header.

    Args:
        app: FastAPI application
        call_next: Next middleware/handler
        request: Request object

    Returns:
            Response
    """
    # Generate request ID if not present
    if not request.headers.get("x-request-id"):
        request.headers["x-request-id"] = (
            f"{request.method}:{request.url}:{request.query_params}"
        )

    return await call_next(request)


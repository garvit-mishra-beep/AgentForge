"""
Centralized exception handling for AgentOS API.

Production-grade HTTP exceptions and handlers.
"""

import logging
from typing import Any

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.api.core.config import settings

from apps.api.core.logging import get_structlog_logger
logger = get_structlog_logger(__name__)


# ===============================
# CUSTOM EXCEPTIONS
# ===============================


class WorkflowException(HTTPException):
    """
    Base exception for workflow-related errors.
    """

    def __init__(
        self,
        workflow_id: str | None = None,
        message: str | None = None,
        code: str | None = None,
        detail: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.workflow_id = workflow_id
        self.message = message or detail
        self.code = code
        self.detail = detail or message or "Workflow error"


class WorkflowNotFoundException(WorkflowException):
    """Workflow not found."""

    def __init__(self, workflow_id: str):
        super().__init__(
            status_code=404,
            workflow_id=workflow_id,
            message="Workflow not found",
            detail=f"Workflow {workflow_id} not found",
        )


class WorkflowAlreadyExistsException(WorkflowException):
    """Workflow already exists."""

    def __init__(self, workflow_id: str):
        super().__init__(
            status_code=409,
            workflow_id=workflow_id,
            message="Workflow already exists",
            detail=f"Workflow {workflow_id} already exists",
        )


class WorkflowTimeoutException(WorkflowException):
    """Workflow execution timed out."""

    def __init__(self, workflow_id: str):
        super().__init__(
            status_code=408,
            workflow_id=workflow_id,
            message="Workflow execution timed out",
            detail="Workflow execution exceeded timeout",
        )


class WorkflowCancelledException(WorkflowException):
    """Workflow was cancelled."""

    def __init__(self, workflow_id: str):
        super().__init__(
            status_code=409,
            workflow_id=workflow_id,
            message="Workflow cancelled",
            detail="Workflow was cancelled by user request",
        )


class WorkflowRetryExhaustedException(WorkflowException):
    """All retries exhausted."""

    def __init__(self, workflow_id: str):
        super().__init__(
            status_code=500,
            workflow_id=workflow_id,
            message="Workflow retry exhausted",
            detail="All retry attempts were exhausted",
        )


class AuthenticationException(WorkflowException):
    """Authentication failed."""

    def __init__(self, message: str | None = None):
        super().__init__(
            status_code=401,
            message=message or "Authentication failed",
            detail=message or "Authentication failed",
        )


class AuthorizationException(WorkflowException):
    """Authorization failed."""

    def __init__(self, message: str | None = None):
        super().__init__(
            status_code=403,
            message=message or "Authorization failed",
            detail=message or "Authorization failed",
        )


class ValidationException(WorkflowException):
    """Validation failed."""

    def __init__(self, errors: dict):
        super().__init__(
            status_code=422,
            message="Validation failed",
            detail=str(errors) if errors else "Validation failed",
        )


class WebSocketException(WorkflowException):
    """WebSocket communication error."""

    def __init__(self, message: str | None = None):
        super().__init__(
            status_code=400,
            message=message or "WebSocket error",
            detail=message or "WebSocket error",
        )


# ===============================
# EXCEPTION HANDLERS
# ===============================


async def exception_handler_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions.

    Args:
        request: Request object
        exc: StarletteHTTPException

    Returns:
        JSONResponse with error details
    """
    logger.exception(
        f"HTTP {exc.status_code}",
        path=str(request.url),
        method=request.method,
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail or "An error occurred",
            "status_code": exc.status_code,
            "path": str(request.url),
        },
        headers={
            "X-Error-Code": exc.detail or "unknown",
        },
    )


async def exception_handler_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle request validation errors.

    Args:
        request: Request object
        exc: RequestValidationError

    Returns:
        JSONResponse with validation errors
    """
    errors = exc.errors()

    logger.exception(
        "Request validation error",
        path=str(request.url),
        method=request.method,
        errors=errors,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "errors": errors,
            "path": str(request.url),
        },
    )


async def exception_handler_pydantic_error(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: Request object
        exc: ValidationError

    Returns:
        JSONResponse with validation errors
    """
    errors = exc.errors()

    logger.exception(
        "Pydantic validation error",
        path=str(request.url),
        method=request.method,
        errors=errors,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "errors": errors,
            "path": str(request.url),
        },
    )


async def exception_handler_internal_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle uncaught exceptions.

    Args:
        request: Request object
        exc: Exception instance

    Returns:
        JSONResponse with error message
    """
    logger.exception(
        "Internal server error",
        path=str(request.url),
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
                "path": str(request.url),
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "status_code": 500,
            "path": str(request.url),
            "request_id": request.headers.get("x-request-id", "unknown"),
        },
    )


# ===============================
# REGISTRY
# ===============================


exception_handlers = {
    StarletteHTTPException: exception_handler_exception,
    RequestValidationError: exception_handler_validation_error,
    ValidationError: exception_handler_pydantic_error,
    Exception: exception_handler_internal_error,
}

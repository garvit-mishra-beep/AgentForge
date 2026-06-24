"""
Centralized logging configuration.

Structured logging with correlation IDs and request context.
"""

import logging
import sys
from datetime import datetime
from typing import Any

import structlog
from structlog.processors import TimeStamper, JSONRenderer

from apps.api.core.config import settings


# ===============================
# LOGGING PROCESSORS
# ===============================


def make_time_stamper():
    """Create time stamper processor."""
    def processor(logger, name, event, **kwargs):
        return {"time": datetime.utcnow().isoformat()}
    return processor


def make_correlation_id():
    """Create correlation ID processor."""
    def processor(logger, name, event, **kwargs):
        return {"correlation_id": event.get("correlation_id", event.get("request_id"))}
    return processor


def add_request_info():
    """Add request info to log events."""
    def processor(logger, name, event, **kwargs):
        return {
            **event,
            "method": event.get("method", "N/A"),
            "endpoint": event.get("endpoint", event.get("event", "N/A")),
        }
    return processor


# ===============================
# STRUCTURED LOGGING BOOTSTRAP
# ===============================


def bootstrap_logging(
    logger: logging.Logger | None = None,
    name: str | None = None,
) -> logging.Logger:
    """
    Bootstrap structured logging.

    Args:
        logger: Optional logger to configure
        name: Optional name for new logger

    Returns:
        logging.Logger: Configured logger
    """
    # Create base logger if not provided
    if logger is None:
        logger = logging.getLogger(name or "agentos")

    # Add console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.LOG_LEVEL)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers = [handler]

    # Build processor chain - simplified and working version
    processors = [
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),

        # Add correlation ID
        make_correlation_id(),

        # Add request info
        add_request_info(),

        # Add exception info (format_exc_info is available)
        structlog.processors.format_exc_info,

        # JSON renderer
        JSONRenderer(),
    ]

    # Configure structlog
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG
        ),
        context_class=dict,
        cache_logger_on_first_use=True,
        processors=processors,
    )

    logger.info("Structured logging configured")
    return logger


def get_structlog_logger(
    name: str | None = None,
    context: dict | None = None,
) -> Any:
    """
    Get structlog logger instance.

    Args:
        name: Logger name
        context: Initial context

    Returns:
        Structured logger
    """
    return structlog.get_logger(
        name=name or "agentos",
        **({} if context is None else context),
    )


# ===============================
# EXCEPTION LOGGING
# ===============================


def log_exception(
    logger: logging.Logger | None = None,
    exc_info: bool | None = None,
    **context,
) -> None:
    """
    Log exception with structured context.

    Args:
        logger: Logger instance
        exc_info: Include exception info
        **context: Additional context
    """
    logger.exception(
        "Exception occurred",
        exc_info=exc_info,
        **context,
    )


def log_error(
    logger: logging.Logger | None = None,
    error: str | Exception | None = None,
    **context,
) -> None:
    """
    Log error message.

    Args:
        logger: Logger instance
        error: Error message or exception
        **context: Additional context
    """
    if error is None:
        error = context.get("message", "Unknown error")

    context["error"] = str(error)
    logger.error(
        "Error occurred",
        **context,
    )


# ===============================
# METRIC LOGGING
# ===============================


def log_metric(
    logger: logging.Logger | None = None,
    metric_name: str = "",
    value: float = 0.0,
    tags: dict | None = None,
    **context,
) -> None:
    """
    Log metric value.

    Args:
        logger: Logger instance
        metric_name: Metric name
        value: Metric value
        tags: Metric tags
        **context: Additional context
    """
    context["metric"] = metric_name
    context["value"] = value
    if tags:
        context.update(tags)

    logger.info("Metric recorded", **context)


# ===============================
# REQUEST LOGGING
# ===============================


def log_request(
    logger: logging.Logger | None = None,
    method: str = "",
    path: str = "",
    status_code: int | None = None,
    duration_ms: float | None = None,
    size_bytes: int | None = None,
    **context,
) -> None:
    """
    Log request/response metrics.

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status
        duration_ms: Request duration
        size_bytes: Response size
        **context: Additional context
    """
    context["method"] = method
    context["path"] = path
    if status_code:
        context["status_code"] = status_code
    if duration_ms:
        context["duration_ms"] = duration_ms
    if size_bytes:
        context["size_bytes"] = size_bytes

    context["event"] = "request_completed"

    logger.info("Request completed", **context)

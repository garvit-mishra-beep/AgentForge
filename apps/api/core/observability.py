"""Observability module with structured logging, metrics, and tracing support.

Emits named events with JSON payloads to the logger at INFO level.
In production, these feed into log aggregation (Datadog, Grafana Loki, etc.).
"""

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ── Structured Events ──────────────────────────────────────────────────


def emit(event: str, data: dict) -> None:
    """Log a structured event.

    Event names:
        review_queued       — review submitted to queue
        review_completed    — pipeline finished successfully
        review_failed       — pipeline raised an exception
        rate_limit_hit      — client was rate-limited (global or review)
        queue_full          — review rejected because queue at capacity
        auth_failed         — authentication failure
        brute_force_lockout — login blocked by brute force protection
        task_started        — agent task execution started
        task_completed      — agent task execution completed
        task_failed         — agent task execution failed
        provider_error      — AI provider returned an error
    """
    logger.info("EVENT %s %s", event, json.dumps(data, default=str))


# ── Request Timing ─────────────────────────────────────────────────────


@dataclass
class RequestMetrics:
    method: str = ""
    path: str = ""
    status_code: int = 0
    duration_ms: float = 0.0
    user_id: str = ""
    correlation_id: str = ""


_request_metrics: list[RequestMetrics] = []


@contextmanager
def track_request(method: str, path: str, user_id: str = ""):
    metrics = RequestMetrics(method=method, path=path, user_id=user_id)
    start = time.monotonic()
    try:
        yield metrics
    finally:
        metrics.duration_ms = (time.monotonic() - start) * 1000
        _request_metrics.append(metrics)
        if len(_request_metrics) > 1000:
            _request_metrics.pop(0)

        emit("request", {
            "method": metrics.method,
            "path": metrics.path,
            "status": metrics.status_code,
            "duration_ms": round(metrics.duration_ms, 2),
            "user_id": metrics.user_id[:8] if metrics.user_id else "",
        })


def get_request_metrics() -> list[RequestMetrics]:
    return list(_request_metrics)


def record_request_metric(method: str, path: str, status_code: int, duration_ms: float, user_id: str = "", correlation_id: str = "") -> None:
    metrics = RequestMetrics(
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        correlation_id=correlation_id,
    )
    _request_metrics.append(metrics)
    if len(_request_metrics) > 1000:
        _request_metrics.pop(0)


# ── Health Metrics ─────────────────────────────────────────────────────


def get_health_metrics() -> dict[str, Any]:
    from core.task_tracker import tracker

    recent = _request_metrics[-100:] if _request_metrics else []
    errors = sum(1 for m in recent if m.status_code >= 500)
    total = len(recent)

    return {
        "active_background_tasks": tracker.active_count,
        "recent_requests": total,
        "recent_errors": errors,
        "error_rate": round(errors / max(total, 1) * 100, 2),
        "average_duration_ms": round(
            sum(m.duration_ms for m in recent) / max(total, 1), 2
        ),
    }


# ── Correlation ID ─────────────────────────────────────────────────────

import uuid


def generate_correlation_id() -> str:
    return str(uuid.uuid4())


def get_correlation_id(headers: dict | None = None) -> str:
    if headers and "x-correlation-id" in headers:
        return headers["x-correlation-id"]
    return generate_correlation_id()

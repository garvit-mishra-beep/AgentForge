"""
Tracing helpers for AgentOS.

Provides distributed tracing capabilities.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from apps.api.core.config import settings
from apps.api.core.logging import get_structlog_logger

logger = get_structlog_logger(__name__)


# ===============================
# TRACE ID
# ===============================


def generate_trace_id() -> str:
    """
    Generate trace ID.

    Returns:
        Trace ID string
    """
    return f"trace-{uuid.uuid4().hex[:16]}"


def generate_span_id() -> str:
    """
    Generate span ID.

    Returns:
        Span ID string
    """
    return f"span-{uuid.uuid4().hex[:8]}"


def get_trace_id() -> str:
    """
    Get trace ID from context or generate new one.

    Returns:
        Trace ID string
    """
    trace_id = None

    # Try to get from headers
    trace_id = headers.get("x-trace-id") or headers.get("traceparent")

    if not trace_id:
        trace_id = generate_trace_id()

    return trace_id


def get_span_id() -> str:
    """
    Get span ID from context.

    Returns:
        Span ID string
    """
    return headers.get("x-span-id", generate_span_id())


def set_span_id(span_id: str) -> None:
    """
    Set span ID.

    Args:
        span_id: Span ID string
    """
    headers["x-span-id"] = span_id


# ===============================
# HEADERS
# ===============================


headers: Dict[str, str] = {
    "x-trace-id": "",
    "x-span-id": "",
    "x-correlation-id": "",
}


# ===============================
# SPAN CONTEXT
# ===============================


class SpanContext:
    """
    Span context for trace propagation.
    """

    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_id: Optional[str] = None,
    ):
        """
        Initialize span context.

        Args:
            trace_id: Trace ID
            span_id: Span ID
            parent_id: Parent span ID
        """
        self.trace_id = trace_id or generate_trace_id()
        self.span_id = span_id or generate_span_id()
        self.parent_id = parent_id or self.span_id
        self.operation_name = ""
        self.kind = "SPAN_KIND_INTERNAL"
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict] = []
        self.parent: Optional["SpanContext"] = None

    @property
    def duration_ms(self) -> float:
        """
        Get span duration in ms.

        Returns:
            Duration in ms
        """
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000

    def tag(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add tag to span.

        Args:
            key: Tag key
            value: Tag value
        """
        self.tags[key] = value

    def log(
        self,
        event: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log event to span.

        Args:
            event: Event name
            data: Event data
        """
        self.logs.append({
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
        })

    def to_dict(self) -> Dict[str, Any]:
        """
        Get span as dictionary.

        Returns:
            Span dictionary
        """
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "operation_name": self.operation_name,
            "kind": self.kind,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "logs": self.logs,
        }


# ===============================
# SPAN
# ===============================


class Span:
    """
    Span for distributed tracing.
    """

    def __init__(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_id: Optional[str] = None,
    ):
        """
        Initialize span.

        Args:
            operation_name: Span operation name
            trace_id: Trace ID
            span_id: Span ID
            parent_id: Parent span ID
        """
        self.context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
        )
        self.context.operation_name = operation_name

        # In production, initialize OpenTelemetry or Jaeger here
        # self._otel_tracer = None

    def __enter__(self) -> "Span":
        """
        Enter span context.

        Returns:
            Span instance
        """
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        """
        Exit span context.
        """
        self.finish(
            error=exc_val is not None,
            exception=exc_val,
        )

    def start(
        self,
    ) -> "Span":
        """
        Start span.

        Returns:
            Span instance
        """
        self.context.start_time = datetime.utcnow()
        return self

    def finish(
        self,
        error: bool = False,
        exception: Optional[Exception] = None,
    ) -> None:
        """
        Finish span.

        Args:
            error: Whether span ended with error
            exception: Exception if any
        """
        self.context.end_time = datetime.utcnow()
        self.context.tags["error"] = error
        self.context.tags["exception"] = str(exception) if exception else None

        logger.debug(
            "Span finished",
            span_id=self.context.span_id,
            duration_ms=self.context.duration_ms,
            error=error,
        )

    def tag(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add tag to span.

        Args:
            key: Tag key
            value: Tag value
        """
        self.context.tag(key, value)

    def log(
        self,
        event: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log event to span.

        Args:
            event: Event name
            data: Event data
        """
        self.context.log(event, data)

    @property
    def duration_ms(self) -> float:
        """
        Get span duration.

        Returns:
            Duration in ms
        """
        return self.context.duration_ms

    @property
    def trace_id(self) -> str:
        """
        Get trace ID.

        Returns:
            Trace ID string
        """
        return self.context.trace_id

    @property
    def span_id(self) -> str:
        """
        Get span ID.

        Returns:
            Span ID string
        """
        return self.context.span_id

    def to_dict(self) -> Dict[str, Any]:
        """
        Get span as dictionary.

        Returns:
            Span dictionary
        """
        return self.context.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        """
        Get span as dictionary.

        Returns:
            Span dictionary
        """
        return self.context.to_dict()


# ===============================
# TRACE
# ===============================


class Trace:
    """
    Trace for distributed tracing.
    """

    def __init__(
        self,
        trace_id: Optional[str] = None,
    ):
        """
        Initialize trace.

        Args:
            trace_id: Trace ID
        """
        self.trace_id = trace_id or generate_trace_id()
        self.spans: List[Span] = []

    def span(
        self,
        operation_name: str,
        parent_id: Optional[str] = None,
    ) -> Span:
        """
        Create span.

        Args:
            operation_name: Span operation name
            parent_id: Parent span ID

        Returns:
            Span instance
        """
        span = Span(
            operation_name=operation_name,
            trace_id=self.trace_id,
            parent_id=parent_id,
        )
        self.spans.append(span)
        return span

    def to_dict(self) -> Dict[str, Any]:
        """
        Get trace as dictionary.

        Returns:
            Trace dictionary
        """
        return {
            "trace_id": self.trace_id,
            "spans": [s.to_dict() for s in self.spans],
        }

    def to_json(self) -> str:
        """
        Get trace as JSON.

        Returns:
            JSON string
        """
        import json

        return json.dumps(self.to_dict(), indent=2)


# ===============================
# GLOBAL TRACER
# ===============================


class Tracer:
    """
    Global tracer for distributed tracing.
    """

    def __init__(self):
        """
        Initialize tracer.
        """
        self._active_spans: List[Span] = []
        self._trace_context: Optional[Trace] = None

    def enter_span(
        self,
        operation_name: str,
        parent_id: Optional[str] = None,
    ) -> Span:
        """
        Enter span.

        Args:
            operation_name: Span operation name
            parent_id: Parent span ID

        Returns:
            Span instance
        """
        span = Span(
            operation_name=operation_name,
            parent_id=parent_id,
        )
        self._active_spans.append(span)
        return span

    def exit_span(
        self,
        span: Optional[Span] = None,
    ) -> None:
        """
        Exit span.

        Args:
            span: Span to exit
        """
        if span:
            span.finish()

            # Remove from active spans
            self._active_spans.remove(span)

        # Log active span count
        logger.debug(
            "Active spans count",
            count=len(self._active_spans),
        )

    def get_trace(self) -> Optional[Trace]:
        """
        Get current trace.

        Returns:
            Current trace or None
        """
        return self._trace_context

    def set_trace(
        self,
        trace: Optional[Trace] = None,
    ) -> None:
        """
        Set current trace.

        Args:
            trace: Trace to set
        """
        self._trace_context = trace

    def get_span_id(self) -> str:
        """
        Get current span ID.

        Returns:
            Span ID string
        """
        if self._active_spans:
            return self._active_spans[-1].span_id
        return generate_span_id()

    def get_trace_id(self) -> str:
        """
        Get current trace ID.

        Returns:
            Trace ID string
        """
        if self._trace_context:
            return self._trace_context.trace_id
        return generate_trace_id()

    def tag_span(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Tag current span.

        Args:
            key: Tag key
            value: Tag value
        """
        if self._active_spans:
            self._active_spans[-1].tag(key, value)


# ===============================
# GLOBAL TRACER INSTANCE
# ===============================


_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """
    Get or create global tracer.

    Returns:
        Tracer instance
    """
    global _tracer

    if _tracer is None:
        _tracer = Tracer()

    return _tracer


def span(
    operation_name: str,
    parent_id: Optional[str] = None,
) -> Span:
    """
    Create and enter span.

    Args:
        operation_name: Span operation name
        parent_id: Parent span ID

    Returns:
        Span instance
    """
    tracer = get_tracer()
    span = tracer.enter_span(operation_name, parent_id)
    return span


def trace(
    operation_name: str,
    parent_id: Optional[str] = None,
) -> Trace:
    """
    Create and enter trace.

    Args:
        operation_name: Trace operation name
        parent_id: Parent trace ID

    Returns:
        Trace instance
    """
    trace = Trace()
    return trace


# ===============================
# INITIALIZATION
# ===============================


def init_tracing(
    endpoint: Optional[str] = None,
    sample_rate: float = 1.0,
) -> None:
    """
    Initialize tracing.

    Args:
        endpoint: Tracing endpoint
        sample_rate: Sample rate (0.0-1.0)
    """
    if endpoint:
        logger.info("Tracing initialized", endpoint=endpoint)
    else:
        logger.info("Tracing initialized (disabled)")

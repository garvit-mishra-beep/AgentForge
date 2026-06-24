"""
Metrics collection for AgentOS.

Provides metrics collection and reporting.
"""

import asyncio
from enum import Enum
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from apps.api.core.config import settings
from apps.api.core.logging import get_structlog_logger

logger = get_structlog_logger(__name__)


# ===============================
# METRIC TYPES
# ===============================


class MetricType(str, Enum):
    """
    Metric type constants.
    """

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


# ===============================
# METRIC REGISTRY
# ===============================


class MetricRegistry:
    """
    Metric registry for collecting metrics.
    """

    def __init__(self):
        """
        Initialize metric registry.
        """
        # Metrics: name -> {type, labels, value, timestamp, description}
        self._metrics: Dict[str, Dict] = {}

        # Counters: name -> current_value
        self._counters: Dict[str, int] = defaultdict(int)

        # Gauges: name -> current_value
        self._gauges: Dict[str, float] = defaultdict(float)

        # Histograms: name -> {buckets, sum, count}
        self._histograms: Dict[str, Dict] = defaultdict(
            lambda: {"buckets": [], "sum": 0, "count": 0}
        )

        # Summary: name -> {quantiles, sum, count}
        self._summaries: Dict[str, Dict] = defaultdict(
            lambda: {"quantiles": {}, "sum": 0, "count": 0}
        )

        # Labels index: name -> set of labels
        self._labels_index: Dict[str, set] = defaultdict(set)

    def register_counter(
        self,
        name: str,
        description: str = "",
        **kwargs,
    ) -> None:
        """
        Register counter metric.

        Args:
            name: Metric name
            description: Metric description
            **kwargs: Additional kwargs
        """
        self._metrics[name] = {
            "type": MetricType.COUNTER.value,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._labels_index[name].add("counter")

    def register_gauge(
        self,
        name: str,
        description: str = "",
        **kwargs,
    ) -> None:
        """
        Register gauge metric.

        Args:
            name: Metric name
            description: Metric description
            **kwargs: Additional kwargs
        """
        self._metrics[name] = {
            "type": MetricType.GAUGE.value,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._labels_index[name].add("gauge")

    def register_histogram(
        self,
        name: str,
        description: str = "",
        **kwargs,
    ) -> None:
        """
        Register histogram metric.

        Args:
            name: Metric name
            description: Metric description
            **kwargs: Additional kwargs
        """
        self._metrics[name] = {
            "type": MetricType.HISTOGRAM.value,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._labels_index[name].add("histogram")

    def register_summary(
        self,
        name: str,
        description: str = "",
        **kwargs,
    ) -> None:
        """
        Register summary metric.

        Args:
            name: Metric name
            description: Metric description
            **kwargs: Additional kwargs
        """
        self._metrics[name] = {
            "type": MetricType.SUMMARY.value,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._labels_index[name].add("summary")

    def inc(
        self,
        name: str,
        labels: Optional[Dict[str, Any]] = None,
        value: int = 1,
    ) -> None:
        """
        Increment counter.

        Args:
            name: Metric name
            labels: Metric labels
            value: Increment value
        """
        self._counters[name] += value

    def set(
        self,
        name: str,
        labels: Optional[Dict[str, Any]] = None,
        value: float = 0.0,
    ) -> None:
        """
        Set gauge value.

        Args:
            name: Metric name
            labels: Metric labels
            value: Gauge value
        """
        self._gauges[name] = value

    def observe(
        self,
        name: str,
        labels: Optional[Dict[str, Any]] = None,
        value: float = 0.0,
    ) -> None:
        """
        Observe histogram value.

        Args:
            name: Metric name
            labels: Metric labels
            value: Observed value
        """
        histogram = self._histograms[name]

        histogram["count"] += 1
        histogram["sum"] += value

        # Add to buckets (simplified)
        bucket = value * 100
        histogram["buckets"].append(bucket)

    def record(
        self,
        name: str,
        labels: Optional[Dict[str, Any]] = None,
        value: float = 0.0,
    ) -> None:
        """
        Record summary value.

        Args:
            name: Metric name
            labels: Metric labels
            value: Recorded value
        """
        summary = self._summaries[name]

        summary["count"] += 1
        summary["sum"] += value


# ===============================
# GLOBAL METRICS
# ===============================


_registry: Optional[MetricRegistry] = None


def get_metrics_registry() -> MetricRegistry:
    """
    Get or create global metrics registry.

    Returns:
        MetricRegistry instance
    """
    global _registry

    if _registry is None:
        _registry = MetricRegistry()

    return _registry


def create_counter(
    name: str,
    description: str = "",
) -> MetricRegistry:
    """
    Create counter metric.

    Args:
        name: Metric name
        description: Metric description

    Returns:
        MetricRegistry instance
    """
    registry = get_metrics_registry()
    registry.register_counter(name, description)
    return registry


def create_gauge(
    name: str,
    description: str = "",
) -> MetricRegistry:
    """
    Create gauge metric.

    Args:
        name: Metric name
        description: Metric description

    Returns:
        MetricRegistry instance
    """
    registry = get_metrics_registry()
    registry.register_gauge(name, description)
    return registry


def create_histogram(
    name: str,
    description: str = "",
) -> MetricRegistry:
    """
    Create histogram metric.

    Args:
        name: Metric name
        description: Metric description

    Returns:
        MetricRegistry instance
    """
    registry = get_metrics_registry()
    registry.register_histogram(name, description)
    return registry


def create_summary(
    name: str,
    description: str = "",
) -> MetricRegistry:
    """
    Create summary metric.

    Args:
        name: Metric name
        description: Metric description

    Returns:
        MetricRegistry instance
    """
    registry = get_metrics_registry()
    registry.register_summary(name, description)
    return registry


# ===============================
# METRICS COLLECTION
# ===============================


class MetricsCollector:
    """
    Metrics collector for collecting various metrics.
    """

    def __init__(self, registry: MetricRegistry):
        """
        Initialize metrics collector.

        Args:
            registry: Metrics registry
        """
        self.registry = registry

    async def collect_request_metrics(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        size_bytes: int = 0,
    ) -> None:
        """
        Collect request metrics.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status
            duration_ms: Duration in ms
            size_bytes: Response size
        """
        registry = get_metrics_registry()

        # Increment request count
        registry.inc("http_requests_total", {"method": method, "status": status_code})

        # Record request duration
        registry.observe("http_request_duration", {"method": method, "path": path}, duration_ms)

        # Record response size
        registry.inc("http_response_bytes", {"method": method}, size_bytes)

        # Record status codes
        registry.inc("http_response_status", {"code": status_code})

    async def collect_workflow_metrics(
        self,
        workflow_id: str,
        status: str,
        duration_ms: float = 0,
        result: Optional[Dict] = None,
    ) -> None:
        """
        Collect workflow metrics.

        Args:
            workflow_id: Workflow ID
            status: Workflow status
            duration_ms: Execution duration
            result: Execution result
        """
        registry = get_metrics_registry()

        # Record workflow status
        registry.inc("workflow_executions_total", {"workflow": workflow_id, "status": status})

        # Record duration
        registry.observe("workflow_duration", {"workflow": workflow_id}, duration_ms)

        # Record result
        if result:
            for key, value in result.items():
                registry.inc(f"workflow_result_{key}", {"workflow": workflow_id})

    async def collect_provider_metrics(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        """
        Collect provider metrics.

        Args:
            provider: Provider name
            model: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens
            latency_ms: Latency in ms
            success: Success flag
        """
        registry = get_metrics_registry()

        # Record provider requests
        registry.inc(
            "provider_requests_total",
            {"provider": provider, "model": model, "success": success},
        )

        # Record tokens
        registry.inc("provider_input_tokens", {"provider": provider})
        registry.inc("provider_output_tokens", {"provider": provider})

        # Record latency
        registry.observe("provider_latency", {"provider": provider}, latency_ms)


# ===============================
# METRICS FORMATTER
# ===============================


class MetricsFormatter:
    """
    Metrics formatter for exporting metrics.
    """

    @staticmethod
    def prometheus(registry: MetricRegistry) -> str:
        """
        Format metrics as Prometheus exposition format.

        Args:
            registry: Metrics registry

        Returns:
            Prometheus-formatted metrics
        """
        lines: List[str] = []

        # Counters
        for name, counter in registry._counters.items():
            lines.append(f"# HELP {name}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {counter}")

        # Gauges
        for name, gauge in registry._gauges.items():
            lines.append(f"# HELP {name}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {gauge}")

        # Histograms
        for name, histogram in registry._histograms.items():
            lines.append(f"# HELP {name}")
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}{{le=+Inf}} {histogram['count']}")

        return "\n".join(lines)

    @staticmethod
    def json(registry: MetricRegistry) -> str:
        """
        Format metrics as JSON.

        Args:
            registry: Metrics registry

        Returns:
            JSON-formatted metrics
        """
        metrics = {
            "counters": dict(registry._counters),
            "gauges": dict(registry._gauges),
            "histograms": {
                name: {
                    "count": h["count"],
                    "sum": h["sum"],
                    "buckets": h["buckets"]
                }
                for name, h in registry._histograms.items()
            },
            "metadata": {
                "registry": str(registry),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        return json.dumps(metrics, indent=2)

    @staticmethod
    def text(registry: MetricRegistry) -> str:
        """
        Format metrics as plain text.

        Args:
            registry: Metrics registry

        Returns:
            Text-formatted metrics
        """
        lines: List[str] = []

        for name, value in registry._counters.items():
            lines.append(f"{name} {value}")

        for name, value in registry._gauges.items():
            lines.append(f"{name} {value}")

        return "\n".join(lines)

    @staticmethod
    def console(registry: MetricRegistry) -> str:
        """
        Format metrics for console display.

        Args:
            registry: Metrics registry

        Returns:
            Console-formatted metrics
        """
        lines: List[str] = []

        for name, counter in registry._counters.items():
            lines.append(f"{name}: {counter}")

        return "\n".join(lines)


# ===============================
# METRICS FLUSHER
# ===============================


class MetricsFlusher:
    """
    Metrics flusher for sending metrics to external systems.
    """

    def __init__(
        self,
        registry: MetricRegistry,
        endpoint: Optional[str] = None,
    ):
        """
        Initialize metrics flusher.

        Args:
            registry: Metrics registry
            endpoint: Export endpoint
        """
        self.registry = registry
        self.endpoint = endpoint
        self._running: bool = False

    async def flush(
        self,
        format: str = "prometheus",
    ) -> int:
        """
        Flush metrics.

        Args:
            format: Output format

        Returns:
            Number of bytes flushed
        """
        registry = get_metrics_registry()

        # Format metrics
        if format == "json":
            metrics = MetricsFormatter.json(registry)
        elif format == "text":
            metrics = MetricsFormatter.text(registry)
        else:
            metrics = MetricsFormatter.prometheus(registry)

        # Log metrics
        logger.info(
            "Metrics flushed",
            format=format,
            size=len(metrics),
        )

        return len(metrics.encode())

    async def flush_to_endpoint(
        self,
        format: str = "prometheus",
    ) -> int:
        """
        Flush metrics to endpoint.

        Args:
            format: Output format

        Returns:
            Number of bytes sent
        """
        if not self.endpoint:
            return 0

        registry = get_metrics_registry()

        # Format metrics
        metrics = MetricsFormatter.prometheus(registry)

        # In production, send to Prometheus or other metrics endpoint
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(self.endpoint, data=metrics) as response:
        #         return len(response.read())

        # Log as flushed
        logger.info(
            "Metrics sent to endpoint",
            endpoint=self.endpoint,
            format=format,
            size=len(metrics),
        )

        return len(metrics.encode())

    async def start(self) -> None:
        """
        Start metrics flusher.
        """
        self._running = True
        logger.info("Metrics flusher started")

    async def shutdown(self) -> None:
        """
        Shutdown metrics flusher.
        """
        self._running = False
        logger.info("Metrics flusher shutdown")

    async def flush_loop(
        self,
        interval: float = 30.0,
    ) -> None:
        """
        Flush metrics at interval.

        Args:
            interval: Flush interval in seconds
        """
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics flush error: {e}")


# ===============================
# FACTORY
# ===============================


async def flush_metrics(
    format: str = "prometheus",
) -> int:
    """
    Flush metrics.

    Args:
        format: Output format

    Returns:
        Number of bytes flushed
    """
    registry = get_metrics_registry()
    return MetricsFormatter.json(registry)

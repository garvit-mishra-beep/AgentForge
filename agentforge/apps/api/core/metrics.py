from __future__ import annotations

import time
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from apps.api.core.config import settings

logger = logging.getLogger(__name__)

_request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

_error_count = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "path", "status"],
)

_workflow_executions = Counter(
    "workflow_executions_total",
    "Total workflow executions",
    ["status"],
)

_workflow_duration = Histogram(
    "workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
    buckets=(0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
)

_agent_invocations = Counter(
    "agent_invocations_total",
    "Total agent invocations",
    ["agent_id", "status"],
)

_token_usage = Counter(
    "token_usage_total",
    "Total token usage",
    ["agent_id", "model"],
)

_rag_queries = Counter(
    "rag_queries_total",
    "Total RAG queries",
    ["status"],
)

_rag_retrieval_latency = Histogram(
    "rag_retrieval_latency_seconds",
    "RAG retrieval latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

_db_connections = Gauge("db_connections_active", "Active database connections")


def track_request(method: str, path: str, status: int, duration: float) -> None:
    _request_count.labels(method=method, path=path, status=status).inc()
    _request_duration.labels(method=method, path=path).observe(duration)
    if status >= 500:
        _error_count.labels(method=method, path=path, status=status).inc()


def track_workflow(workflow_id: str, status: str, duration: float) -> None:
    _workflow_executions.labels(status=status).inc()
    _workflow_duration.labels(workflow_id=workflow_id).observe(duration)


def track_agent_invocation(agent_id: str, status: str) -> None:
    _agent_invocations.labels(agent_id=agent_id, status=status).inc()


def track_token_usage(agent_id: str, model: str, tokens: int) -> None:
    _token_usage.labels(agent_id=agent_id, model=model).inc(tokens)


def track_rag_query(status: str, latency: float) -> None:
    _rag_queries.labels(status=status).inc()
    _rag_retrieval_latency.observe(latency)


def metrics_endpoint():
    return generate_latest(REGISTRY)

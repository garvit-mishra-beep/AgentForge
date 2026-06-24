# Observability

## Overview

AgentForge AI provides three pillars of observability:

1. **Metrics** — Prometheus-based performance and operational metrics
2. **Tracing** — OpenTelemetry distributed tracing
3. **Logging** — Structured logging with structlog

## Metrics

### Available Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `http_requests_total` | Counter | method, path, status | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | method, path | Request latency |
| `http_errors_total` | Counter | method, path, status | HTTP 5xx errors |
| `workflow_executions_total` | Counter | status | Workflow execution count |
| `workflow_duration_seconds` | Histogram | workflow_id | Workflow execution duration |
| `agent_invocations_total` | Counter | agent_id, status | Agent invocation count |
| `token_usage_total` | Counter | agent_id, model | LLM token consumption |
| `rag_queries_total` | Counter | status | RAG query count |
| `rag_retrieval_latency_seconds` | Histogram | — | RAG retrieval latency |
| `db_connections_active` | Gauge | — | Active database connections |

### Metrics Endpoint

```
GET /metrics
```

Returns Prometheus-formatted text. Configurable via `ENABLE_METRICS` env var (default: `true`).

### Custom Buckets

Histogram buckets are tuned per operation:
- **HTTP requests**: 5ms → 10s
- **RAG retrieval**: 10ms → 5s
- **Workflow execution**: 100ms → 120s

## Distributed Tracing

### Configuration

```env
ENABLE_TRACING=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Instrumented Libraries
- **FastAPI** — HTTP request spans
- **HTTPX** — Outbound HTTP call spans
- **SQLAlchemy** — Database query spans

### Trace Export

Uses OTLP HTTP protocol (not gRPC) for broader backend compatibility. Compatible with:
- Jaeger
- Grafana Tempo
- SigNoz
- OpenTelemetry Collector

## Structured Logging

### Configuration

```env
LOG_LEVEL=INFO
ENABLE_JSON_LOGS=true   # JSON format for production
```

### Log Format

Development (human-readable, colored):
```
2025-01-01T00:00:00.000Z [info     ] Request processed     method=GET path=/api/v1/health status=200 duration_ms=12.3
```

Production (JSON):
```json
{
  "event": "Request processed",
  "level": "info",
  "timestamp": "2025-01-01T00:00:00.000Z",
  "logger": "apps.api.middleware.logging",
  "method": "GET",
  "path": "/api/v1/health",
  "status": 200,
  "duration_ms": "12.3"
}
```

### Logged Events
- **Request lifecycle**: method, path, status code, duration
- **Auth events**: token creation, verification, expiration, rejection
- **Rate limiting**: exceeded requests
- **Audit failures**: non-blocking audit log errors
- **Health checks**: service status changes
- **Retries**: circuit breaker state changes, retry attempts
- **Errors**: structured error context with traceback

## Health Checks

### Endpoints

| Endpoint | Checks | Purpose |
|---|---|---|
| `/api/v1/live` | Process only | Liveness probe |
| `/api/v1/ready` | Database only | Readiness probe |
| `/api/v1/health` | All services | Full health status |

### Check Categories

| Check | Critical | Service |
|---|---|---|
| database | Yes | PostgreSQL |
| redis | No | Redis |
| qdrant | No | Qdrant |

A non-critical failure sets overall status to `degraded`. Critical failure sets it to `unhealthy`.

## Resilience

### Circuit Breakers

| Service | Fail Max | Reset Timeout |
|---|---|---|
| LLM | 5 | 60s |
| Qdrant | 3 | 30s |
| Redis | 3 | 30s |

### Retry Policies

| Service | Max Attempts | Backoff | Timeout |
|---|---|---|---|
| LLM | 3 | 1s → 10s exponential | 60s |
| Qdrant | 2 | 1s → 5s exponential | 30s |
| Redis | 2 | 1s → 3s exponential | 5s |

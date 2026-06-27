# Observability Guide — AgentForge

**Last Updated:** June 2026

---

## Structured Logging

All services use structured JSON logging with the following standard fields:

```json
{
  "timestamp": "2026-06-25T12:00:00.000Z",
  "level": "INFO",
  "service": "api",
  "task_id": "task_abc123",
  "agent_id": "agent_backend_001",
  "role": "backend",
  "model": "claude-sonnet-4-6",
  "duration_ms": 7123,
  "token_count": 1500,
  "event": "agent_complete",
  "message": "Backend Engineer completed JWT auth implementation",
  "metadata": {
    "files_created": 3,
    "confidence": 0.92
  }
}
```

### Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed debugging information (not emitted in production) |
| `INFO` | Normal operational events (task created, step started/completed) |
| `WARNING` | Unexpected but handled situations (retry triggered, rate limit approaching) |
| `ERROR` | Errors that need attention but don't crash the service (API key invalid, model timeout) |
| `CRITICAL` | Service-level failures (database unreachable, Redis connection lost) |

### Python Logging Setup

```python
# apps/api/core/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if DEBUG else structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

---

## OpenTelemetry Tracing

### Trace Propagation

W3C `traceparent` header propagates across service boundaries:

```
Next.js (Browser) → FastAPI (REST/WS) → LangGraph Node → AI Provider API
     ↑                    ↓                    ↓
  traceparent:      traceparent:          span per
  00-abc...-def...   00-abc...-ghi...      AI call
```

### Spans

| Span Name | Parent | Description |
|-----------|--------|-------------|
| `task.execute` | Root | Full task execution |
| `node.{role_name}` | `task.execute` | Single agent node execution |
| `node.{role_name}.prompt_render` | `node.{role_name}` | Jinja2 template rendering |
| `node.{role_name}.ai_call` | `node.{role_name}` | AI provider API call |
| `node.{role_name}.validate` | `node.{role_name}` | Output validation pipeline |
| `node.{role_name}.db_write` | `node.{role_name}` | Persisting output to PostgreSQL |
| `ws.event.{event_type}` | Root (WS connection) | WebSocket event publishing |

### Enabling Local Tracing

```bash
# Start Jaeger (UI: http://localhost:16686)
docker compose -f docker-compose.observability.yml up -d

# Set env vars
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=agentforge-api

# Restart API — traces appear in Jaeger automatically
```

---

## Prometheus Metrics

### Metrics Exported (on `/metrics` endpoint)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentforge_task_duration_seconds` | Histogram | `status`, `complexity` | Time from task creation to completion |
| `agentforge_task_total` | Counter | `status` | Total tasks created |
| `agentforge_agent_errors_total` | Counter | `role`, `model`, `error_type` | Agent step errors |
| `agentforge_model_latency_seconds` | Histogram | `model`, `role` | AI provider API latency |
| `agentforge_model_tokens_total` | Counter | `model`, `type` (input/output) | Cumulative token usage |
| `agentforge_ws_connections_active` | Gauge | — | Current WebSocket connections |
| `agentforge_ws_events_total` | Counter | `event_type` | WebSocket events published |
| `agentforge_db_pool_size` | Gauge | — | Current asyncpg pool size |
| `agentforge_db_query_duration_seconds` | Histogram | `query_type` | Database query latency |
| `agentforge_redis_cache_hit_ratio` | Gauge | `cache_name` | Redis cache hit rate (0-1) |

---

## Grafana Dashboard

### Recommended Panels

| Panel | Metric | Visualization |
|-------|--------|--------------|
| Task Completion Rate | `agentforge_task_total{status="completed"}` / `agentforge_task_total` | Stat (percentage) |
| Task Duration P50/P95/P99 | `agentforge_task_duration_seconds` | Heatmap |
| Active Tasks | `agentforge_task_total{status!="completed"}` | Time series |
| Agent Error Rate | `rate(agentforge_agent_errors_total[5m])` | Time series by role |
| Model Latency | `agentforge_model_latency_seconds{p50}` | Bar chart by model |
| Token Usage | `rate(agentforge_model_tokens_total[5m])` | Stacked area |
| WebSocket Connections | `agentforge_ws_connections_active` | Gauge |
| Database Pool | `agentforge_db_pool_size` | Gauge |
| Redis Cache Hit Ratio | `agentforge_redis_cache_hit_ratio` | Time series |

---

## Alerting Rules

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| High Task Error Rate | `rate(agentforge_agent_errors_total[5m]) > 0.1` | Warning | Slack |
| Task Duration P99 > 5 min | `agentforge_task_duration_seconds{p99} > 300` | Warning | Slack |
| Agent Error Spike | `rate(agentforge_agent_errors_total[1m]) > 0.5` | Critical | PagerDuty |
| High Model Latency | `agentforge_model_latency_seconds{p95} > 30` | Warning | Slack |
| DB Connection Pool Exhausted | `agentforge_db_pool_size == max_pool` | Critical | PagerDuty |
| Redis Down | `redis_up == 0` | Critical | PagerDuty |
| WebSocket Connections Spike | `rate(agentforge_ws_connections_active[1m]) > 100` | Warning | Slack |

---

## Local Observability Stack

```yaml
# docker-compose.observability.yml
version: "3.8"
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4318:4318"    # OTLP HTTP

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
```

```bash
# Start
docker compose -f docker-compose.observability.yml up -d

# URLs:
# Jaeger:  http://localhost:16686
# Prom:    http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

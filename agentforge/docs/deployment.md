# Deployment Guide

## Docker Deployment

### Build Images

```bash
# Build all services
docker compose build

# Build individual services
docker compose build api
docker compose build web
```

### Run in Production Mode

```yaml
# docker-compose.prod.yml
services:
  api:
    build:
      context: .
      dockerfile: infrastructure/docker/api.Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - JWT_SECRET=${JWT_SECRET}
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}
      - REDIS_URL=redis://${REDIS_HOST}:6379/0
      - QDRANT_URL=http://${QDRANT_HOST}:6333
      - LLM_PROVIDER=${LLM_PROVIDER}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENABLE_METRICS=true
      - ENABLE_JSON_LOGS=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

```bash
# Start production stack
docker compose -f docker-compose.prod.yml up -d
```

## Environment Variables (Production)

| Variable | Required | Notes |
|---|---|---|
| `JWT_SECRET` | **Yes** | Generate with `openssl rand -hex 32` |
| `DATABASE_URL` | **Yes** | Use connection pooling (pgbouncer recommended) |
| `REDIS_URL` | **Yes** | Redis with TLS recommended |
| `QDRANT_URL` | **Yes** | Qdrant Cloud or self-hosted |
| `LLM_PROVIDER` | No | Set based on your model provider |
| `OPENAI_API_KEY` | Conditional | Store in secrets manager |
| `ENABLE_METRICS` | No | Enable for production monitoring |
| `ENABLE_JSON_LOGS` | No | Set to `true` for log aggregation |
| `ENABLE_TRACING` | No | Enable for distributed tracing |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |

## Production Checklist

See [production-checklist.md](production-checklist.md) for a comprehensive production readiness checklist.

## Scaling Considerations

### API Service
- Horizontally scalable via stateless design
- Session state stored in Redis
- Rate limiting uses in-memory store (consider Redis for multi-replica)

### Database
- Connection pooling via SQLAlchemy (`pool_size=20`, `max_overflow=10`)
- Migrations via Alembic (non-blocking)
- Read replicas for analytics queries

### Vector Store
- Qdrant supports horizontal scaling
- Collection replication factor configurable

### Caching
- Redis for session cache and WebSocket pub/sub
- Connection timeout: 5 seconds

## Monitoring

### Prometheus Metrics
Available at `/metrics` endpoint. Key metrics:
- `http_requests_total` — Request count by method, path, status
- `http_request_duration_seconds` — Request latency histogram
- `workflow_executions_total` — Workflow execution count
- `agent_invocations_total` — Agent invocation count
- `token_usage_total` — LLM token usage
- `rag_queries_total` — RAG query count

### Health Checks
- `/api/v1/live` — Liveness probe (always healthy if process is running)
- `/api/v1/ready` — Readiness probe (checks database only)
- `/api/v1/health` — Full health check (database, Redis, Qdrant)

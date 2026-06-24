# Docker Validation Guide

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│  PostgreSQL  │
│   :3000     │     │   :8000      │     │   :5432     │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐     ┌─────────────┐
                    │    Redis     │     │   Qdrant    │
                    │   :6379      │     │   :6333     │
                    └──────────────┘     └─────────────┘
```

## Quick Start

```bash
# Build and start all services
docker compose up --build -d

# Check service health
docker compose ps
docker compose logs api

# Run migrations
docker compose exec api alembic upgrade head

# Verify
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
```

## Service Dependencies

| Service    | Depends On          | Health Check             |
|-----------|---------------------|--------------------------|
| postgres  | —                   | pg_isready               |
| redis     | —                   | redis-cli ping           |
| qdrant    | —                   | TCP :6333                |
| api       | postgres, redis, qdrant | FastAPI /api/v1/health |
| web       | api                 | Next.js :3000            |

## Health Checks

### PostgreSQL
```bash
docker compose exec postgres pg_isready -U agentforge
```

### Redis
```bash
docker compose exec redis redis-cli ping
# Expected: PONG
```

### API
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy", "environment": "development", ...}
```

### Web
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Expected: 200
```

## Environment Configuration

### Required Variables

| Variable       | Default                                          | Description          |
|---------------|--------------------------------------------------|----------------------|
| DATABASE_URL  | postgresql+asyncpg://agentforge:agentforge@postgres:5432/agentforge | PostgreSQL connection |
| REDIS_URL     | redis://redis:6379/0                             | Redis connection     |
| QDRANT_URL    | http://qdrant:6333                               | Qdrant connection    |
| JWT_SECRET    | (must be set)                                    | JWT signing secret   |

### Optional Variables

| Variable            | Default           | Description              |
|--------------------|-------------------|--------------------------|
| ENVIRONMENT         | development       | Runtime environment      |
| LOG_LEVEL           | INFO              | Logging level            |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30    | JWT access token TTL     |
| REFRESH_TOKEN_EXPIRE_DAYS  | 7      | JWT refresh token TTL    |

## Startup Ordering

docker-compose.yml enforces:
1. postgres (health check: pg_isready)
2. redis (health check: redis-cli ping)
3. qdrant (condition: service_started)
4. api (depends_on all above)
5. web (depends_on: api)

## Data Persistence

| Volume            | Mount                          | Service   |
|------------------|--------------------------------|-----------|
| postgres_data    | /var/lib/postgresql/data       | postgres  |
| redis_data       | /data                          | redis     |
| qdrant_data      | /qdrant/storage                | qdrant    |

## Troubleshooting

### API container exits immediately
```bash
docker compose logs api
# Check for: JWT_SECRET not set, database connection refused
```

### Database connection refused
```bash
# Verify postgres is healthy
docker compose exec postgres pg_isready -U agentforge
# Check connection string in api logs
```

### Migrations not applied
```bash
docker compose exec api alembic upgrade head
docker compose exec api alembic current
```

### Qdrant connection failed
```bash
docker compose exec qdrant curl -s http://localhost:6333/health
```

### Web cannot reach API
```bash
# Verify NEXT_PUBLIC_API_URL matches the API's external address
# Default: http://localhost:8000/api/v1
```

## Common Failures

1. **Port conflicts** — Ensure :3000, :5432, :6379, :6333, :8000 are free
2. **JWT_SECRET** — Must be set; application exits if empty or default
3. **Alembic migrations** — `create_all` is bypassed in production; run `alembic upgrade head`
4. **Volume permissions** — On Linux, postgres may need `chown 999:999` on pgdata
5. **Resource limits** — Minimum 2GB RAM recommended for all services

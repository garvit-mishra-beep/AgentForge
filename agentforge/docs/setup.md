# Setup Guide

## Prerequisites

- **Python 3.12+** (see `.python-version`)
- **Node.js 20+** (see `package.json` engines)
- **Docker & Docker Compose** (for infrastructure: PostgreSQL, Redis, Qdrant)
- **Make** (optional, for convenience commands)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/agentforge.git
cd agentforge

# Copy environment configuration
cp .env.example .env

# Edit .env with your settings (at minimum set JWT_SECRET and LLM API keys)
# Edit .env

# Start infrastructure services
docker compose up -d postgres redis qdrant

# Install backend dependencies
cd apps/api
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET` | **Yes** | — | HMAC key for JWT signing (min 32 bytes) |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection string |
| `QDRANT_URL` | Yes | `http://localhost:6333` | Qdrant vector database URL |
| `LLM_PROVIDER` | No | `openai` | LLM provider (`openai`, `anthropic`, `google`) |
| `OPENAI_API_KEY` | Conditional | — | Required if `LLM_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | Conditional | — | Required if `LLM_PROVIDER=anthropic` |
| `GEMINI_API_KEY` | Conditional | — | Required if `LLM_PROVIDER=google` |
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `ENABLE_TRACING` | No | `false` | Enable OpenTelemetry tracing |
| `ENABLE_METRICS` | No | `true` | Enable Prometheus metrics |
| `ENABLE_JSON_LOGS` | No | `false` | JSON-formatted structured logging |

## Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","version":"0.1.0",...}

# API root
curl http://localhost:8000/
# Expected: {"service":"AgentForge AI","docs":"/docs","api":"/api/v1"}
```

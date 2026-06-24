# AgentForge AI

FastAPI backend for AI agent orchestration.

## Development

```bash
# Start infrastructure
docker compose up -d postgres redis qdrant

# Start the API
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /api/v1/health` — Health check
- `POST /api/v1/auth/token` — Login
- `GET/POST /api/v1/agents` — Agent CRUD
- `POST /api/v1/agents/:id/invoke` — Invoke agent
- `GET/POST /api/v1/workflows` — Workflow CRUD
- `POST /api/v1/workflows/:id/execute` — Execute workflow
- `GET /api/v1/executions` — Execution history
- `GET /api/v1/observability/usage` — Usage metrics

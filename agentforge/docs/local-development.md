# Local Development Guide

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Web UI     │────▶│   API         │────▶│  PostgreSQL  │
│  (Next.js)   │     │  (FastAPI)    │     │              │
└──────────────┘     │              │     ├──────────────┤
                     │              │────▶│    Redis     │
┌──────────────┐     │              │     │  (Cache/WS)  │
│  External    │────▶│              │     ├──────────────┤
│  Clients     │     │              │────▶│   Qdrant     │
└──────────────┘     │              │     │(Vector DB)   │
                     └──────────────┘     └──────────────┘
```

## Starting Infrastructure

```bash
# Start all services
docker compose up -d

# Start individual services (if you want to run API locally)
docker compose up -d postgres redis qdrant

# Verify services
docker compose ps
```

## Starting the API

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with hot-reload
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000/docs` (Swagger UI).

## Starting the Web UI

```bash
cd apps/web

# Install dependencies
npm install

# Start dev server
npm run dev
```

The web UI will be available at `http://localhost:3000`.

## Makefile Commands

```bash
make dev          # Start Docker services + API
make dev-api      # Start API locally
make dev-web      # Start web UI
make test         # Run all tests
make lint         # Lint code
make seed         # Seed database
make clean        # Clean up
```

## Database Migrations

```bash
make migrate              # Apply pending migrations
make migrate-revision     # Create new migration
make migrate-downgrade    # Rollback one migration
make migrate-current      # Show current revision
make migrate-history      # Show migration history
```

## Testing

```bash
# Run all tests
cd apps/api && pytest

# Run with coverage
cd apps/api && pytest --cov=apps/api

# Run specific test file
cd apps/api && pytest tests/unit/test_security.py

# Run tests matching pattern
cd apps/api && pytest -k "health or metrics"
```

## Code Quality

```bash
# Lint API
cd apps/api && ruff check .

# Lint web
cd apps/web && npm run lint

# Type check
npm run type-check
```

## Common Issues

### Database connection refused
Ensure PostgreSQL is running: `docker compose up -d postgres`

### Qdrant client warning
The warning "Failed to obtain server version" is harmless in development. Set `QDRANT_URL` correctly in `.env`.

### Port conflicts
Default ports: API=8000, Web=3000, Postgres=5432, Redis=6379, Qdrant=6333

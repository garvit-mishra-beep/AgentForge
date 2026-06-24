# Database Migration Guide

## Overview

AgentForge uses Alembic for database migrations. Migrations are in `apps/api/alembic/`.

## Commands

```bash
# Run all pending migrations
cd apps/api && alembic upgrade head

# Rollback one migration
cd apps/api && alembic downgrade -1

# Check current migration state
cd apps/api && alembic current

# View migration history
cd apps/api && alembic history

# Auto-generate a new migration
cd apps/api && alembic revision --autogenerate -m "description"
```

## Makefile

```bash
make migrate          # upgrade head
make migrate-downgrade  # downgrade -1
make migrate-revision message="desc"  # new migration
make migrate-current    # show current
make migrate-history    # show history
```

## Workflow

### Development
1. Modify models in `apps/api/models/__init__.py`
2. Run `make migrate-revision message="description"`
3. Review the generated migration in `apps/api/alembic/versions/`
4. Run `make migrate` to apply
5. Test against local PostgreSQL

### Staging / Production
1. Review migration SQL before applying
2. Run `alembic upgrade head` as part of deployment
3. Verify with `alembic current`

## Initial Setup

The initial migration (`001_initial_schema.py`) creates all 5 tables:
- `users` — User accounts with bcrypt password hashes
- `agents` — AI agent configurations
- `workflows` — Workflow definitions
- `api_keys` — API key authentication
- `executions` — Execution records with foreign keys to agents/workflows

## Auto-migration vs Alembic

Set `AUTO_MIGRATE=false` to disable `create_all` on startup (recommended for
production). The application will then require `alembic upgrade head` to be
run explicitly.

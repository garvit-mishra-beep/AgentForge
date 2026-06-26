# Sprint 1 — Foundation

**Duration:** 5 days | **Focus:** Backend foundation, database, CRUD

---

## Sprint Goal

Boot the backend. Connect to PostgreSQL. Create teams. Create tasks. Everything works via curl by Friday.

---

## Day 1: Monorepo & Infrastructure

### Task 1.1: Initialize monorepo

**Files to create:**
- `package.json` — root workspace config
- `pnpm-workspace.yaml` — workspace definition
- `turbo.json` — pipeline configuration
- `tsconfig.json` — base TypeScript config
- `.gitignore` — ignore node_modules, .env, __pycache__, .turbo
- `.prettierrc` — format config

**Acceptance criteria:**
- [ ] `pnpm install` installs all workspace dependencies
- [ ] `pnpm dev` runs (even if apps don't exist yet)
- [ ] Project structure matches FOLDER_STRUCTURE.md

### Task 1.2: FastAPI skeleton

**Files to create:**
- `apps/api/requirements.txt`
- `apps/api/pyproject.toml`
- `apps/api/app/__init__.py`
- `apps/api/app/main.py` — FastAPI app with CORS middleware and `/health` endpoint

**Acceptance criteria:**
- [ ] `pip install -r requirements.txt` installs all deps
- [ ] `uvicorn app.main:app --reload` starts on port 8000
- [ ] `GET /health` returns `{"status": "ok", "timestamp": "..."}`

### Task 1.3: Docker Compose

**Files to create:**
- `docker-compose.yml` — PostgreSQL 16 service

**Acceptance criteria:**
- [ ] `docker compose up -d` starts PostgreSQL
- [ ] `psql -h localhost -U agentforge -d agentforge -c "SELECT 1"` works
- [ ] Database persists data across container restarts (volume mount)

---

## Day 2: Database

### Task 1.4: Database migration

**Files to create:**
- `apps/api/migrations/001_initial.sql` — full schema from SCHEMA.sql

**Acceptance criteria:**
- [ ] Migration runs without errors
- [ ] All 6 tables created
- [ ] All constraints, indexes, enums, and views created
- [ ] `\dt` shows `users`, `teams`, `team_members`, `tasks`, `task_messages`, `executions`

### Task 1.5: Database connection pool

**Files to create:**
- `apps/api/core/__init__.py`
- `apps/api/core/config.py` — pydantic-settings with `DATABASE_URL`
- `apps/api/core/database.py` — asyncpg pool init, query helper, migration runner

**Acceptance criteria:**
- [ ] Pool initializes on app startup (lifespan event)
- [ ] Pool closes on app shutdown
- [ ] `database.fetch()` and `database.execute()` helpers work
- [ ] Migration runs automatically on startup (idempotent: `CREATE TABLE IF NOT EXISTS`)
- [ ] Connection errors are logged but don't crash the app

### Task 1.6: Configuration

**Files to modify:**
- `apps/api/core/config.py` — add all env vars

**Acceptance criteria:**
- [ ] All `AGENTFORCE_*` env vars loaded
- [ ] Missing required vars raise clear error on startup
- [ ] Optional vars fall back to defaults

---

## Day 3: Models & Teams API

### Task 1.7: Pydantic schemas

**Files to create:**
- `apps/api/models/__init__.py`
- `apps/api/models/schemas.py` — all request/response models

**Models needed:**
- `TeamCreate(name: str, description: str | None)`
- `TeamResponse(id, name, description, members, created_at)`
- `TeamMemberCreate(role: AgentRole, model: str)`
- `TeamMemberResponse(id, team_id, role, model)`
- `TaskCreate(team_id: str, title: str, description: str)`
- `TaskResponse(id, team_id, title, description, status, created_at, updated_at, completed_at, error_message)`
- `TaskMessageResponse(id, task_id, step_order, role, model, message_type, content, created_at)`

**Acceptance criteria:**
- [ ] All models have type hints
- [ ] Validation errors return 422 with clear messages
- [ ] UUIDs validated as strings (parseable to UUID)

### Task 1.8: Teams CRUD

**Files to create:**
- `apps/api/app/routes/__init__.py`
- `apps/api/app/routes/health.py` — health endpoint
- `apps/api/app/routes/teams.py` — team CRUD

**Endpoints:**

```
POST   /api/v1/teams              → 201 + TeamResponse
GET    /api/v1/teams              → 200 + list[TeamResponse]
GET    /api/v1/teams/{id}         → 200 + TeamResponse (with members)
PUT    /api/v1/teams/{id}         → 200 + TeamResponse
DELETE /api/v1/teams/{id}         → 204

POST   /api/v1/teams/{id}/members   → 201 + TeamMemberResponse
DELETE /api/v1/teams/{id}/members/{mid} → 204
```

**Business rules:**
- Team must have exactly 3 members (team_lead, builder, reviewer) to be used
- Cannot add duplicate role to a team
- Deleting a team cascades to members
- Model must be one of the supported models from config

**Acceptance criteria:**
- [ ] All CRUD operations work via curl
- [ ] 404 returned for non-existent teams
- [ ] 409 returned for duplicate role assignment
- [ ] 400 returned for invalid role name
- [ ] Team response includes nested members array

---

## Day 4: Tasks API

### Task 1.9: Tasks CRUD

**Files to create:**
- `apps/api/app/routes/tasks.py` — task CRUD

**Endpoints:**

```
POST   /api/v1/tasks              → 201 + TaskResponse (status = "pending")
GET    /api/v1/tasks              → 200 + list[TaskResponse] (sorted by created_at DESC)
GET    /api/v1/tasks/{id}         → 200 + TaskResponse (with messages nested)
GET    /api/v1/tasks/{id}/messages → 200 + list[TaskMessageResponse] (sorted by step_order)
```

**Business rules:**
- Creating a task validates that the team has all 3 members
- Task starts with status "pending"
- Task status can be polled via GET /tasks/{id}

**Acceptance criteria:**
- [ ] Creating a task requires valid team_id
- [ ] 400 returned if team doesn't have all 3 members
- [ ] Task list returns newest first
- [ ] Messages endpoint returns empty array for new task

---

## Day 5: Tests & Integration

### Task 1.10: Integration tests

**Files to create:**
- `apps/api/tests/__init__.py`
- `apps/api/tests/conftest.py` — pytest fixtures (test DB, test client)
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_teams.py`
- `apps/api/tests/test_tasks.py`

**Test coverage targets:**
- Health endpoint: 100%
- Teams CRUD: 90%+ (all endpoints, all error cases)
- Tasks CRUD: 90%+ (create, list, detail, messages, validation)

**Acceptance criteria:**
- [ ] `pytest` runs all tests
- [ ] Tests use isolated test database (separate PostgreSQL database)
- [ ] Each test cleans up after itself
- [ ] No tests hit real AI providers

---

## Definition of Done (Sprint 1)

- [ ] Backend boots with `uvicorn app.main:app`
- [ ] PostgreSQL runs in Docker
- [ ] Health check returns 200
- [ ] Can create a team with curl
- [ ] Can add 3 members to a team with curl
- [ ] Can create a task with curl
- [ ] Can poll task status with curl
- [ ] All CRUD endpoints return correct status codes
- [ ] Integration tests pass (90%+ coverage on routes)
- [ ] `git push` to `main` — CI passes

---

## Sprint 1 Commands

```bash
# Start infrastructure
docker compose up -d

# Install Python deps
cd apps/api && pip install -r requirements.txt

# Run migration
psql -h localhost -U agentforge -d agentforge -f migrations/001_initial.sql

# Start dev server
uvicorn app.main:app --reload --port 8000

# Test health
curl http://localhost:8000/health

# Create a team
curl -X POST http://localhost:8000/api/v1/teams \
  -H 'Content-Type: application/json' \
  -d '{"name": "Dev Team", "description": "My AI team"}'

# Run tests
cd apps/api && python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## Day-by-Day Success Criteria

| Day | What should be working by EOD |
|-----|------------------------------|
| Day 1 | `docker compose up`, `uvicorn app.main:app`, `curl /health` returns 200 |
| Day 2 | Tables exist in PostgreSQL, pool connects on startup, migration runs automatically |
| Day 3 | `POST /api/v1/teams` returns 201, `GET /api/v1/teams` returns list, team member assignment works |
| Day 4 | `POST /api/v1/tasks` returns 201, `GET /api/v1/tasks/{id}/messages` returns messages |
| Day 5 | `pytest` passes with 90%+ coverage, all CRUD operations verified end-to-end |

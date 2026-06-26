# Implementation Plan — AgentForge MVP

**Total estimated effort:** 4-6 weeks (single engineer)
**Goal:** Working prototype with 3-agent team execution loop

---

## Phase 1: Foundation (Week 1)

**Goal:** Bootable backend with database, CRUD routes, and health check.

### Tasks

| # | Task | Est. Time | Dependencies |
|---|------|-----------|--------------|
| 1.1 | Initialize monorepo structure (pnpm workspaces, turborepo, git) | 2h | None |
| 1.2 | Create `apps/api/` FastAPI skeleton with health endpoint | 3h | 1.1 |
| 1.3 | Write `docker-compose.yml` with PostgreSQL 16 | 1h | None |
| 1.4 | Write database migration `001_initial.sql` | 2h | 1.3 |
| 1.5 | Implement `core/database.py` — asyncpg pool, run migration | 3h | 1.4 |
| 1.6 | Implement `core/config.py` — pydantic-settings env loader | 1h | 1.2 |
| 1.7 | Implement Pydantic schemas in `models/schemas.py` | 2h | 1.5 |
| 1.8 | Implement `routes/teams.py` — CRUD for teams + members | 4h | 1.7 |
| 1.9 | Implement `routes/tasks.py` — create, list, detail, messages | 4h | 1.7 |
| 1.10 | Write integration tests for all CRUD routes | 4h | 1.8, 1.9 |

**Phase 1 deliverable:** Backend boots. `GET /health` returns 200. Can create teams, add members, create tasks via curl.

### Verification

```bash
docker compose up -d                    # Start PostgreSQL
cd apps/api && uvicorn app.main:app     # Start API
curl http://localhost:8000/health       # → {"status": "ok"}
curl -X POST http://localhost:8000/api/v1/teams \
  -H 'Content-Type: application/json' \
  -d '{"name": "My Team", "description": "Test team"}'  # → 201
```

---

## Phase 2: Agent System (Week 2)

**Goal:** LangGraph graph that calls real AI models and produces output.

### Tasks

| # | Task | Est. Time | Dependencies |
|---|------|-----------|--------------|
| 2.1 | Implement `core/providers.py` — OpenAI, Anthropic, Google adapters | 4h | 1.2 |
| 2.2 | Write Jinja2 prompt templates (team_lead, builder, reviewer) | 3h | None |
| 2.3 | Implement `agents/nodes/team_lead_node.py` | 3h | 2.1, 2.2 |
| 2.4 | Implement `agents/nodes/builder_node.py` | 3h | 2.1, 2.2 |
| 2.5 | Implement `agents/nodes/reviewer_node.py` | 3h | 2.1, 2.2 |
| 2.6 | Implement `agents/graph.py` — LangGraph StateGraph with 4 nodes + edges | 3h | 2.3, 2.4, 2.5 |
| 2.7 | Implement `agents/orchestrator.py` — background task executor | 4h | 2.6, 1.9 |
| 2.8 | Write unit tests for each agent node (mocked AI provider) | 4h | 2.3, 2.4, 2.5 |
| 2.9 | Write integration test for full graph execution (mocked AI) | 3h | 2.6, 2.7 |

**Phase 2 deliverable:** Creating a task triggers LangGraph execution. Messages are written to `task_messages`. Task status transitions: pending → running → completed.

### Verification

```bash
# Create a team with 3 members
curl -X POST http://localhost:8000/api/v1/teams \
  -H 'Content-Type: application/json' \
  -d '{"name": "Dev Team", "description": "My AI team"}'
# → team_id

curl -X POST http://localhost:8000/api/v1/teams/{team_id}/members \
  -H 'Content-Type: application/json' \
  -d '{"role": "team_lead", "model": "gemini-1.5-pro"}'

curl -X POST http://localhost:8000/api/v1/teams/{team_id}/members \
  -H 'Content-Type: application/json' \
  -d '{"role": "builder", "model": "claude-sonnet-4-20250514"}'

curl -X POST http://localhost:8000/api/v1/teams/{team_id}/members \
  -H 'Content-Type: application/json' \
  -d '{"role": "reviewer", "model": "gpt-4o"}'

# Submit a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"team_id": "{team_id}", "title": "Build JWT Auth", "description": "Create a FastAPI JWT authentication module with login, refresh, and token validation endpoints."}'
# → task_id

# Poll for completion (every 2 seconds)
curl http://localhost:8000/api/v1/tasks/{task_id}
# → {"status": "completed", ...}

# View messages
curl http://localhost:8000/api/v1/tasks/{task_id}/messages
# → [4 messages: plan, code, review, delivery]
```

---

## Phase 3: Frontend (Week 3)

**Goal:** Functional Next.js UI for team management and task execution.

### Tasks

| # | Task | Est. Time | Dependencies |
|---|------|-----------|--------------|
| 3.1 | Initialize Next.js 15 app with Tailwind, TypeScript strict | 2h | 1.1 |
| 3.2 | Create `lib/api.ts` — typed fetch wrapper for all endpoints | 2h | 3.1 |
| 3.3 | Create basic UI primitives (button, card, input, select, badge, skeleton) | 3h | 3.1 |
| 3.4 | Build team list page + create team page | 4h | 3.2, 3.3 |
| 3.5 | Build team detail page with member management | 4h | 3.2, 3.3 |
| 3.6 | Build task list page | 2h | 3.2, 3.3 |
| 3.7 | Build task execution view with polling + timeline | 6h | 3.2, 3.3 |
| 3.8 | Implement execution timeline component (step-by-step with status) | 4h | 3.7 |
| 3.9 | Implement agent message display component | 2h | 3.7 |
| 3.10 | Add loading states, empty states, error handling | 3h | 3.4-3.9 |
| 3.11 | Add frontend integration tests (vitest + testing-library) | 4h | 3.4-3.9 |

**Phase 3 deliverable:** Full UI flow: Create team → assign models → submit task → watch execution in real-time timeline → view results.

### User Flow

```
Dashboard
  ├── "Create Team" → TeamForm (name, description)
  │     └── Team Detail → add 3 members (role + model selector)
  │           └── "Create Task" → TaskForm (title, description)
  │                 └── Task Execution View
  │                       ├── Step 1: Team Lead Planning    [spinner → checkmark]
  │                       ├── Step 2: Builder Working       [spinner → checkmark]
  │                       ├── Step 3: Reviewer Reviewing    [spinner → checkmark]
  │                       └── Step 4: Final Delivery        [spinner → checkmark]
  │                             └── Full message content displayed
  └── "View History" → Task list with status badges
```

---

## Phase 4: Polish & Test (Week 4)

**Goal:** Production-quality error handling, retries, and test coverage.

### Tasks

| # | Task | Est. Time | Dependencies |
|---|------|-----------|--------------|
| 4.1 | Implement retry logic for AI provider calls (2 retries, exponential backoff) | 2h | 2.1 |
| 4.2 | Implement timeout enforcement (MAX_STEPS=20, wall-clock 10min) | 2h | 2.7 |
| 4.3 | Add proper error handling in all agent nodes | 3h | 2.3-2.5 |
| 4.4 | Write comprehensive backend tests (80%+ coverage on agents/) | 6h | 2.8, 2.9 |
| 4.5 | Write E2E test with Playwright (create team → task → verify output) | 4h | 3.4-3.9 |
| 4.6 | Add request logging middleware | 1h | 1.2 |
| 4.7 | Build Dockerfile for FastAPI backend | 2h | 1.2 |
| 4.8 | Set up CI/CD (GitHub Actions: lint → test → build) | 3h | 4.7 |
| 4.9 | Performance test: 10 concurrent tasks, measure completion times | 2h | 4.2 |
| 4.10 | Bug bash — fix all discovered issues before demo | 4h | 4.1-4.9 |

**Phase 4 deliverable:** Production-quality MVP. Tested, documented, demo-ready.

---

## Timeline Summary

```
Week 1: ████████████████░░░░░░░░░░░░  Phase 1 — Foundation
Week 2: ████████████████████░░░░░░░░  Phase 2 — Agent System  
Week 3: ██████████████████████░░░░░░  Phase 3 — Frontend
Week 4: ████████████████████████████  Phase 4 — Polish & Test
```

- Day 1-5: Backend foundation (DB, CRUD, tests)
- Day 6-10: Agent execution (LangGraph, providers, prompts)
- Day 11-15: Frontend (pages, components, API integration)
- Day 16-20: Polish (error handling, tests, CI/CD, perf)

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| AI provider API key not configured | High | High | Validate API keys on team creation; provide clear error messages |
| LangGraph API changes during development | Medium | Medium | Pin LangGraph version; use stable API surface |
| AI provider rate limits hit during testing | Medium | Medium | Implement exponential backoff before first release |
| Frontend polling creates DB load | Low (MVP scale) | Low | Add 2s minimum poll interval; optimize DB query |
| Multi-agent output quality is poor | Medium | Critical | Build evaluation framework in Phase 2; iterate on prompts |

# ONBOARDING — AgentForge

**Goal:** Make a new engineer productive within **30 minutes** of cloning the
repo.

> Already familiar with the stack? Skip to
> [Architecture Overview](#2-architecture-overview) (5 min) and
> [Test Loop](#5-test-loop) (10 min).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Repository Tour](#3-repository-tour)
4. [Local Setup (15 min)](#4-local-setup-15-min)
5. [Test Loop](#5-test-loop)
6. [Debugging Workflow](#6-debugging-workflow)
7. [Deployment Workflow](#7-deployment-workflow)
8. [What to Read Next](#8-what-to-read-next)

---

## 1. Prerequisites

| Tool | Min version | Check |
|------|-------------|-------|
| Python | 3.11 | `python3 --version` |
| Node.js | 22 | `node --version` |
| pnpm | 9 | `pnpm --version` |
| Docker | 24+ | `docker --version` |
| PostgreSQL client | 15+ | `psql --version` |
| Git | 2.40+ | `git --version` |
| Make | any | `make --version` |

Platform notes:

- **Windows:** Use WSL2 for Docker and a POSIX shell. PowerShell works for the
  documented `make` targets; some agents assume Unix-style paths.
- **macOS:** Postgres can be installed via `brew install postgresql@16` if you
  don't want to use Docker.

---

## 2. Architecture Overview

AgentForge is a single API + two thin clients.

```mermaid
graph LR
  Web[apps/web<br/>Next.js 15] -- REST + WS --> API[apps/api<br/>FastAPI]
  CLI[apps/cli<br/>agentforge] -- REST --> API
  API --> PG[(PostgreSQL + pgvector)]
  API --> Redis[(Redis)]
  API --> LLM[(LLM Providers)]
  API --> GH[(GitHub App)]
```

When a user submits a task, the API loads **team config**, fetches
**repository context** (chunks from uploaded files), pulls **relevant memories**
(via pgvector), and runs the **LangGraph StateGraph**:

```
team_lead_plan → builder → [reviewer, tester, security]  → aggregator → team_lead_deliver
   (parallel fan-out)
```

Every node's state is persisted to `executions.graph_state` and streamed to
the UI. The user watches agents collaborate in real time.

Read [`docs/architecture/SYSTEM_ARCHITECTURE.md`](../architecture/SYSTEM_ARCHITECTURE.md)
for the full diagrammed tour.

---

## 3. Repository Tour

```
AgentForge/
├── apps/
│   ├── api/                 # Backend (Python)
│   ├── web/                 # Frontend (TypeScript)
│   └── cli/                 # Terminal (Python)
├── docs/                    # Active documentation
│   ├── architecture/        # SYSTEM_ARCHITECTURE, schema, prompts
│   ├── api/                 # REST + WS reference
│   ├── development/         # ONBOARDING (you are here), conventions
│   ├── deployment/          # CI/CD + ops
│   ├── security/            # SECURITY_MODEL, runbook, privacy
│   ├── product/             # PRD, roadmap, pricing
│   ├── README.md
│   ├── DOCUMENTATION_INDEX.md
│   ├── CHANGELOG.md
│   └── TERMS_OF_USE.md
├── archive/                 # Historical artifacts (read-only)
├── scripts/                 # Cross-app operational scripts
├── .github/workflows/       # CI
├── Dockerfile               # API container
├── docker-compose.yml       # Local Postgres stack
├── Makefile                 # Convenience targets
└── README.md                # Project landing page
```

Top files you'll touch first:

- `apps/api/app/main.py` — middleware stack, router registration.
- `apps/api/agents/orchestrator.py` — task execution driver.
- `apps/api/agents/graph.py` — LangGraph wiring.
- `apps/api/core/config.py` — environment variables.
- `apps/web/app/page.tsx` — Quick Review landing page.

---

## 4. Local Setup (15 min)

### Step 1: Clone & configure (1 min)

```bash
git clone https://github.com/agentforge/agentforge.git
cd agentforge
cp apps/api/.env.example apps/api/.env
```

Generate secrets (you'll paste them into `apps/api/.env`):

```bash
python -c "import secrets; print('AGENTFORGE_JWT_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('AGENTFORGE_JWT_REFRESH_SECRET=' + secrets.token_urlsafe(32))"
python -c "import base64, os; print('AGENTFORGE_ENCRYPTION_KEY=' + base64.b64encode(os.urandom(32)).decode())"
```

### Step 2: Boot Postgres (1 min)

```bash
docker compose up -d
```

Verify: `docker compose ps` should show `agentforge-postgres` healthy.

### Step 3: Install Python deps (2 min)

```bash
make install
# equivalent to: cd apps/api && pip install -r requirements.txt
```

### Step 4: Install Node deps (2 min)

```bash
pnpm install
```

### Step 5: Run the API (1 min)

```bash
make dev
# equivalent to: cd apps/api && uvicorn app.main:app --reload --port 8000
```

You should see `AgentForge API started (auth=True, fast_demo=...)` once
migrations complete. Verify:

```bash
curl http://localhost:8000/api/v1/health
```

### Step 6: Run the Web (1 min)

In another terminal:

```bash
pnpm dev:web
# or: cd apps/web && pnpm dev
```

Open http://localhost:3000 — you should see the Quick Review page.

### Step 7: Run the CLI (optional, 1 min)

```bash
cd apps/cli
pip install -e .
agentforge --help
```

---

## 5. Test Loop

```bash
# Backend tests
make test

# Frontend type-check
make typecheck

# Lint + format
make lint
make format

# Pre-commit hooks
make pre-commit-install
make pre-commit
```

What each target does:

| Target | Runs |
|--------|------|
| `make install` | `pip install -r apps/api/requirements.txt` |
| `make test` | `pytest apps/api/tests -v --cov=…` |
| `make lint` | `ruff check apps/api` |
| `make format` | `ruff format apps/api` |
| `make typecheck` | `tsc --noEmit` in `apps/web` |
| `make security` | `bandit` + `safety` |
| `make benchmark` | `python -m benchmarks.runner` |
| `make eval` | `python -m evals.harness` |

When writing a new test:

1. Co-locate under `apps/api/tests/test_*.py`.
2. Use fixtures from `conftest.py`.
3. Mirror the file under test (e.g. `app/routes/tasks.py` → `tests/test_tasks.py`).
4. See `docs/development/TESTING.md` for conventions.

---

## 6. Debugging Workflow

### API

- **Logs:** structured JSON (or text), every request gets a correlation ID.
  Filter by `correlation_id`.
- **Metrics:** `curl http://localhost:8000/api/v1/metrics` — Prometheus format.
- **Health:** `curl http://localhost:8000/api/v1/health`.
- **Breakpoints:** use `debugpy` — `python -m debugpy --listen 0.0.0.0:5678 -m
  uvicorn app.main:app --reload`.
- **DB:** `psql postgresql://agentforge:agentforge@localhost:5432/agentforge`.

### Agent graph

- Each execution's full state is in `executions.graph_state` (JSONB).
- Messages are in `task_messages`.
- Memories are in `agent_memories`.
- Add `logger.debug("…", extra={...})` calls in nodes; correlation ID
  auto-propagates.

### Common gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| `AUTH_JWT_SECRET required` | missing env | set it in `apps/api/.env` |
| Migrations don't run | DB unreachable | check `docker compose ps` |
| `langchain` import error | leftover dep | `pip uninstall langchain -y` |
| 401 from web | expired token | clear localStorage, re-login |
| Slow graph | large context | reduce `MAX_CONTEXT_MESSAGES` or upload fewer files |

See `docs/development/OBSERVABILITY.md` for the full surface.

---

## 7. Deployment Workflow

Read [`docs/deployment/DEPLOYMENT.md`](../deployment/DEPLOYMENT.md) for the
canonical steps. Quick version:

```bash
# 1. Build image
docker build -t agentforge-api:latest -f Dockerfile .

# 2. Push
docker push <registry>/agentforge-api:latest

# 3. Roll out
kubectl apply -f k8s/   # or your platform's manifest
```

CI: every push runs `.github/workflows/ci.yml` (lint + test + build).

---

## 8. What to Read Next

| Path | Time | Why |
|------|------|-----|
| [`docs/architecture/SYSTEM_ARCHITECTURE.md`](../architecture/SYSTEM_ARCHITECTURE.md) | 10 min | Understand the whole system |
| [`docs/development/CONVENTIONS.md`](../development/CONVENTIONS.md) | 5 min | Match the surrounding code style |
| [`docs/api/API.md`](../api/API.md) | 10 min | Know the public contract |
| [`docs/security/SECURITY_MODEL.md`](../security/SECURITY_MODEL.md) | 8 min | Don't accidentally bypass a guard |
| [`apps/api/agents/graph.py`](../../apps/api/agents/graph.py) | 5 min | See the actual graph wiring |

Welcome aboard — file your first PR!

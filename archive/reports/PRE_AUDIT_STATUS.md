# Pre-Audit Validation Status

**Classification:** PARTIAL

> The repository is structurally sound and some components are functional, but critical infrastructure dependencies (PostgreSQL, Redis) are unavailable, and the Python `requirements.txt` is significantly out of date. Auditing features that require database access or external services will be blocked.

---

## 1. Repository Structure — ✅ PASS

Git monorepo with three main apps and supporting modules:

| Path | Purpose |
|------|---------|
| `apps/api/` | FastAPI backend (26 route files, core services, agent orchestration) |
| `apps/web/` | Next.js 15 frontend (19 pages, Radix UI components) |
| `apps/cli/` | CLI tool |
| `app/` | Supporting Python packages (validation, evidence_gate, repository_intelligence) |
| `docs/` | Architecture, development, deployment docs |
| `scripts/` | Test and verification scripts |
| `migrations/` | SQL migration files |
| `uploads/` | User file upload storage |

---

## 2. Dependencies Install — ⚠️ PARTIAL

### Frontend (npm) — ✅ PASS
- `npm install` succeeds (403 packages, 0 vulnerabilities)
- All dependencies including Next.js 15, React 19, Radix UI, Tailwind CSS 4, Framer Motion

### Backend (pip) — ❌ FAIL — MAJOR BLOCKER
- `apps/api/requirements.txt` is **severely out of date**
- Pins very old versions (fastapi 0.104.1, pydantic 2.5.0, langchain 0.1.5, langgraph 0.0.22) that conflict with the actual codebase
- Fresh install from `requirements.txt` fails due to unresolvable dependency resolution
- **Missing requirements**: `SQLAlchemy`, `PyJWT`, `pytest`, `pytest-asyncio`, `pytest-httpx` are used by the code but not listed
- **Wrong requirements**: `python-jose` listed but code uses `PyJWT` (`import jwt`)
- Workaround: A venv was built with relaxed version ranges to enable partial testing

---

## 3. Backend Starts — ⚠️ PARTIAL

- **App import**: ✅ Succeeds — `from app.main import app` imports cleanly
- **Config loading**: ✅ Works — settings load and validate from `.env`
- **Server startup**: ❌ Blocked — requires PostgreSQL on `localhost:5432` and Redis on `localhost:6379`
- App tries to connect to both services in the `lifespan` handler before serving requests
- Cannot start standalone without `docker compose up postgres redis`

---

## 4. Frontend Builds — ✅ PASS

- `npm run build` (Next.js production build) succeeds
- Compiled in 6.7s with zero errors
- 19 pages generated (static + dynamic)
- Warnings only: 8 `react-hooks/exhaustive-deps` warnings (missing `load`/`options` deps in `useEffect`/`useCallback`)
- Lint warnings: ESLint plugin not detected in config (cosmetic)

---

## 5. Tests Execute — ⚠️ PARTIAL

- **208 tests total** discovered across 20 test files
- **87 tests (42%) pass** — all non-database-dependent tests:
  - `test_health.py` ✅ (1/1)
  - `test_agent_outputs.py` ✅ (8/8)
  - `test_validation.py` ✅ (10/10)
  - `test_prompt_injection.py` ✅ (7/7)
  - `test_file_parser.py` ✅ (9/9)
  - `test_security.py` ✅ (26/26)
  - `test_graph.py` ✅ (5/5)
  - `test_providers.py` ✅ (8/8)
  - `test_feedback.py` ✅ (6/6)
- **121 tests (58%) skipped** — require PostgreSQL database and/or Redis:
  - `test_auth.py` (11 tests)
  - `test_benchmark.py` (6 tests)
  - `test_concurrency.py` (4 tests)
  - `test_e2e_full_flow.py` (9 tests)
  - `test_evals.py` (2 tests)
  - `test_executions.py` (5 tests)
  - `test_github.py` (7 tests)
  - `test_keys.py` (14 tests)
  - `test_memory_service.py` (13 tests)
  - `test_migrations.py` (1 test)
  - `test_projects_authz.py` (4 tests)
  - `test_review.py` (12 tests)
  - `test_review_load.py` (4 tests)
  - `test_task_tracker.py` (4 tests)
  - `test_tasks.py` (9 tests)
  - `test_teams.py` (16 tests)

---

## 6. Docker Configuration Parses — ✅ PASS

- `docker-compose.yml` validates as valid YAML
- Three services defined: `postgres` (16-alpine), `redis` (7-alpine), `api` (custom Dockerfile)
- Health checks, volume mounts, environment variable wiring all present
- `Dockerfile` for API builds correctly (two-stage: builder + runtime with non-root user)

---

## 7. Environment Variables Discoverable — ✅ PASS

- **`.env.example`**: Comprehensive, with all variables documented by category (backend, auth, demo mode, frontend)
- **`.env`**: Active config with dev defaults (JWT secrets set, auth enabled, fast demo mode on)
- **`apps/api/.env`** and **`apps/api/.env.example`**: Also present with API-specific overrides
- Self-documenting: comments explain what each variable does and how to generate values

---

## Blockers Summary

| # | Blocker | Impact | Fix Required |
|---|---------|--------|-------------|
| 1 | **PostgreSQL not running** | Cannot start backend server; 121 tests blocked | `docker compose up postgres` |
| 2 | **Redis not running** | Rate limiting, caching, and worker features unavailable | `docker compose up redis` |
| 3 | **`requirements.txt` out of date** | Fresh install fails; pinned versions don't match actual imports; missing packages | Regenerate requirements from actual imports |
| 4 | **Wrong JWT library** | `python-jose` pinned but `PyJWT` is used | Update requirements.txt |
| 5 | **Missing test dependencies** | `pytest-asyncio`, `pytest-httpx`, `httpx` not in requirements.txt | Add to test dependencies |

---

## Verdict

**PARTIAL** — The codebase is structurally sound, the frontend builds and runs, and core unit tests (42%) execute successfully. However, full validation of backend features, database-dependent routes, and integration tests requires PostgreSQL and Redis services (blockers 1-2). The dependency drift (blockers 3-5) must be resolved before the project can be reliably audited or deployed.

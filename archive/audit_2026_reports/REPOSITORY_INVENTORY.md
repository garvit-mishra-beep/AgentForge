# AgentForge — Repository Inventory (2026-06-26)

> A `REPOSITORY_INVENTORY.md` already existed in the repo root; this is an independently
> re-counted version. Counts exclude `node_modules`, `__pycache__`, `.next`, caches, and the
> 64 `uploads/*` fixture dirs.

## Coverage statement (mandatory rule)
The audit read/analyzed the full source surface: **131 Python files** (excl. caches) and
**60 TS/TSX files** (excl. node_modules), all **13 SQL migrations**, all infra
(Dockerfile, docker-compose, .github CI, Makefile, pyproject, package.json), and the key docs.
The `uploads/` tree (64 dirs of `hello.py`/`auth_service.py` fixtures) and the 522MB
`AgentForge.zip` were inventoried but not line-read (they are artifacts, not source). The ~40
self-authored `.md` reports were skimmed and treated as marketing, not evidence. Effective source
coverage **> 95%**. Proceeding with the audit.

## Counts
| Area | Count |
|---|---|
| Python source files (excl caches/uploads) | 131 |
| TS/TSX source files (excl node_modules) | 60 |
| Frontend route pages (`app/**/page.tsx`) | 20 |
| Frontend components | 32 |
| Backend API route modules (`app/routes/*`) | 11 |
| AI agent node modules (`agents/nodes/*`) | 7 |
| Core infra modules (`core/*`) | 10 |
| DB migrations (`migrations/*.sql`) | 13 |
| Python test files (`tests/test_*`) | 17 (≈167 tests) |
| Root self-audit `.md` reports | 43 |
| Upload fixture dirs | 64 |

## Subsystem map
- **Auth/security:** `app/auth.py`, `routes/auth.py`, `routes/keys.py`, `core/encryption.py`, `core/config.py`, `core/redis.py` (rate limit/brute force)
- **Agent system:** `agents/graph.py`, `orchestrator.py`, `state.py`, `utils.py`, `nodes/{team_lead,builder,reviewer,tester,security,architect,aggregator}_node.py`, `prompts/*.jinja2`
- **Memory:** `app/memory_service.py`, `routes/memories.py`, `migrations/009_memories.sql`
- **Analytics:** `routes/analytics.py`, `migrations/008_analytics.sql`, `migrations/011`
- **Projects/files/context:** `routes/projects.py`, `routes/context.py`, `app/file_parser.py`, `migrations/006,007`
- **Observability:** `core/observability.py`, `core/logging_config.py`, `routes/health.py`, `core/task_tracker.py`
- **Frontend:** `apps/web/app/*` (20 pages), `components/*` (32), `lib/{api,types,constants,demo-data,templates,utils}.ts`

## Entry points
- **API:** `apps/api/app/main.py` (FastAPI app + lifespan: migrations, Redis init, task tracker).
- **Agent execution:** `apps/api/agents/orchestrator.py` `run_task()` → `agents/graph.py` StateGraph.
- **Frontend:** `apps/web/app/layout.tsx` → providers → `app/page.tsx` (landing).
- **Build/infra:** `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, `Makefile`, `turbo.json`.

## Core architecture files (most important to read first)
`app/main.py` · `agents/graph.py` · `agents/orchestrator.py` · `core/config.py` · `core/database.py` ·
`app/auth.py` · `core/encryption.py` · `core/redis.py` · `app/memory_service.py` · `routes/projects.py` ·
`routes/tasks.py` · `routes/review.py` · `models/schemas.py` · `apps/web/lib/api.ts` ·
`apps/web/components/auth/auth-context.tsx`.

## Request lifecycle (task execution)
`POST /tasks` (`routes/tasks.py`) → validate team roles → INSERT task → `tracker.create_task(run_task)`
→ `orchestrator.run_task` loads task + retrieves memories → `graph.astream` runs
`team_lead_plan → builder → {reviewer,tester,security,architect} → aggregator → team_lead_deliver`
(each node → `call_with_timeout` → provider SDK) → persist execution/messages → store memories.

## Notable hygiene issues
- 522MB `AgentForge.zip` committed in the working tree.
- 43 overlapping self-audit markdown files in root.
- Git remote points at an unrelated `JAVA.git` repo (this tree is not properly version-controlled as AgentForge).

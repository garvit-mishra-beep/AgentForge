# AgentForge — Architecture Audit (Backend / DB / Frontend / DevOps / Testing)

## Backend (FastAPI)

**Good (verified):**
- Async throughout; asyncpg pool (`core/database.py`, min=2/max=10).
- **All SQL is parameterized** (`$1,$2,…`) — spot-checked 50+ queries, no string-interpolated values.
- Pydantic validation on most request bodies (`models/schemas.py`) with length/regex constraints.
- File-upload validation: sanitized filename, extension allowlist, size cap, `resolve()` traversal guard.

**Problems:**
- **No service/repository layer.** Routes call `db.fetch/execute` directly and embed business logic.
  Example: `routes/projects.py:511-581` `_trigger_context_parse` does parsing + `DELETE`/`INSERT`
  inside a fire-and-forget `asyncio.create_task` with no completion callback to update file status.
  → hard to test, reuse, or reason about; logic is duplicated across routes.
- **Memory WHERE clause built by string join** (`memory_service.py:~98-104`): `' AND '.join(conditions)`.
  Values are still parameterized, so not injectable today, but it's a fragile pattern.
- **Broad `except Exception`** that masks real errors:
  - `routes/projects.py:210-211` treats *any* exception on insert as "already assigned" (409).
  - `app/file_parser.py:366-367` swallows all read errors into `content = ""` with no log.
  - `app/auth.py:45-49` `verify_password` returns `False` on any exception, unlogged.
- **Authorization gaps** — see SECURITY_AUDIT.md (file-download IDOR, task-creation IDOR). Several
  `UPDATE`/`DELETE` in `orchestrator.py:79-194` are scoped only by `task_id`, not `created_by`
  (defense-in-depth gap; the calling route does check, so not currently exploitable via HTTP).

## Database

- 13 migrations (`migrations/001…013`), normalized schema, FKs with `ON DELETE CASCADE`, sensible
  constraints. Good baseline.
- **Missing indexes on hot filter columns:**
  - `tasks(created_by)` — `routes/tasks.py:91` filters `WHERE created_by = $1`; only `idx_tasks_team`
    and `idx_tasks_status` exist (`migrations/001_initial.sql`). → seq scan as tasks grow.
  - `executions(created_by)` — column added in `migrations/010` with **no index**; analytics filters
    on it (`routes/analytics.py:43,93,125`).
  - *Fix:* one migration adding both indexes.
- Indexes that **do** exist and are correct: `idx_projects_created_by`, `idx_teams_created_by`,
  `idx_api_keys_user_id`, `idx_memories_user`, `idx_project_teams_*`, `idx_analytics_events_user`.
- Migration runner is invoked on every boot (`main.py:54 pool.run_migrations()`) with **no advisory
  lock** → concurrent instance starts can race. Use `pg_advisory_lock` around migration.
- Migration `005` seeds the demo user with a **SHA-256** password hash; `013` migrates to bcrypt.
  If `013` doesn't run, the demo account is weak. Make bcrypt-only an asserted invariant on boot.
- No N+1 patterns found — list endpoints use explicit JOINs (`analytics.py:140-152`).

## Frontend (Next.js 15 App Router)

**Good:** modern stack (Radix + Tailwind + Framer Motion), clean UI primitives, consistent
loading/empty/error states on most pages, responsive (mobile sidebar sheet), polished landing/demo.

**Problems (verified):**
- **`"use client"` on essentially every page** (`app/page.tsx:1`, `dashboard/page.tsx:1`,
  `tasks/page.tsx:1`, …) → no SSR/RSC benefit, larger hydration cost.
- **Data fetching via `useEffect` everywhere** (`dashboard/page.tsx:35-39`, etc.) — no SWR/react-query,
  so no caching/dedup/retry; race conditions and stale data likely.
- **Quick-Review logic duplicated 3×** (`app/page.tsx:49-114`, `dashboard/page.tsx:21-96`,
  `review/page.tsx:14-78`) — extract a hook.
- **No client-side route protection** — logged-out users can open `/dashboard`,`/teams`,`/tasks`;
  pages just fail their API calls (`lib/api.ts` 401 path refreshes but never redirects on final 401).
- **Tokens in `localStorage`** (`components/auth/auth-context.tsx:39-41`) — XSS → full token theft.
- **Dead code:** `components/status-dot.tsx` and `components/ui/skeleton.tsx` are defined but never
  imported.
- **A11y gaps:** icon-only buttons lack `aria-label` (`sidebar.tsx:96`, `topbar.tsx:96`); no focus
  trap/restoration in modals. Focus-visible rings and label/input pairing are done correctly.

## DevOps

- **Dockerfile:** multi-stage, `python:3.11-slim`, **non-root user**, HEALTHCHECK present. Good.
- **docker-compose:** postgres + api only — **Redis is missing** though the app needs it at boot
  (P0-ops). Postgres auto-runs `001_initial.sql` via init dir; later migrations rely on the boot runner.
- **CI (`.github/workflows/ci.yml`):** lint + typecheck(web) + pytest(+cov) + bandit + safety + docker
  build. Reasonable breadth, but **gates are cosmetic**: pre-commit `|| true`, Safety
  `continue-on-error: true`, Codecov `fail_ci_if_error: false`. No Python type-checking (mypy/pyright).
- **Observability:** structured JSON logging with correlation IDs (`core/logging_config.py`), an
  `emit()` event helper and `/metrics` (`core/observability.py`). **But metrics are an in-memory
  list capped at 1000** (`observability.py:51,63-64`) and `/health` reports from the last ~100
  requests — per-process, lost on restart, useless across instances. No tracing (no OpenTelemetry).
- **No graceful-shutdown alignment:** `tracker.shutdown(timeout=30)` (`main.py:69`) vs Docker's 10s
  default SIGTERM grace → in-flight LLM calls get SIGKILLed.

## Scalability (the structural blocker)

In-memory state that breaks horizontal scaling:
- Rate limits / brute-force / Quick-Review store fall back to process memory (`core/redis.py:60,117,165`).
- Task tracker is per-instance (`core/task_tracker.py:14-15`); `/metrics` active count is per-process.
- Metrics buffer is per-process (above).
- Blocking file I/O in async paths (`projects.py:275-276` `open().write()`; `file_parser.py:363`
  `path.read_text()`).

→ Works fine single-instance; behind a load balancer, rate limits are bypassable and metrics/state
fragment. Externalize all of it to Redis/DB and offload blocking I/O.

## Testing

- **167 tests / ~2,700 LOC**, 17 files. Strong on: auth, keys, teams, review, security, encryption,
  concurrency, providers, validation, memory_service, file_parser, e2e happy path.
- **Untested at the route layer:** `/projects/*` and `/context/*` (the file-upload + parsing surface —
  exactly where the IDOR and blocking-I/O issues live), and `/memories`/`/analytics` HTTP routes
  (logic tested via service, not via the API + auth).
- **Mock-heavy:** providers and graph nodes are mocked (correct for unit speed) but there are **no
  failure-path integration tests** (LLM timeout, DB outage, provider 5xx). Some assertions are thin
  (`test_health.py` only checks `status == "ok"`; `test_providers.py` has `except Exception: pass`).
- Coverage computed but **not enforced** (Codecov non-blocking).

## Verdict (per layer)

| Layer | Score | One-line |
|---|---:|---|
| Backend | 5.0 | Clean async/SQL; no service layer; IDOR + broad excepts |
| Database | 6.0 | Solid schema; missing hot-path indexes; unlocked migrations |
| Frontend | 5.5 | Modern + polished; all-client, useEffect fetching, dup logic, localStorage auth |
| DevOps | 4.5 | Good Docker/CI shell; Redis missing in compose; in-mem metrics; cosmetic gates |
| Testing | 5.5 | Good core coverage; project/context routes & failure paths untested |

The architecture is a **competent single-instance MVP**. The two things standing between it and a
scalable, trustworthy backend are (1) **authorization correctness** and (2) **externalizing
in-memory state + offloading blocking I/O**. Both are bounded, well-understood fixes.

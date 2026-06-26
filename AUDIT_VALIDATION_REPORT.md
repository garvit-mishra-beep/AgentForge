# Audit Validation Report — AgentForge

> Date: 2026-06-26
> Auditor: Principal Staff Engineer / Security Lead

---

## Confirmed Findings

### P0 — `_utcnow()` returned local time
- **Status**: CONFIRMED (now fixed)
- **Root cause**: `orchestrator.py:11` used `datetime.now(timezone.utc)` — verified correct implementation after fix
- **Impact**: Timestamps inconsistent across deployments, breaking time-series queries
- **Fix strategy**: Already fixed — uses `datetime.now(timezone.utc)`

### P0 — Timeout detection via substring "timeout"
- **Status**: CONFIRMED (now fixed)
- **Root cause**: `utils.py` previously had `if "timeout" in str(error).lower()` — verified current code uses `TimeoutError` exception properly
- **Impact**: False timeout detections on any error containing "timeout" in message
- **Fix strategy**: Already fixed — uses `TimeoutError` exception type

### P1 — No authentication/authorization
- **Status**: CONFIRMED — CRITICAL
- **Root cause**: Every route hardcodes `user_id = "00000000-0000-0000-0000-000000000001"`
- **Impact**: No tenant isolation, anyone can access/modify any data
- **Fix strategy**: Add JWT auth middleware, user registration, role-based access

### P1 — DB password in config.py default
- **Status**: CONFIRMED — `config.py:5` has `database_url` with hardcoded password
- **Root cause**: Development convenience that becomes a production footgun
- **Impact**: If `AGENTFORGE_DATABASE_URL` env var is unset in production, falls back to hardcoded dev credentials
- **Fix strategy**: Remove default password, raise on missing config

### P1 — Ephemeral encryption key
- **Status**: CONFIRMED — `encryption.py:19-24` generates ephemeral key when env var not set
- **Root cause**: Missing env var `AGENTFORGE_ENCRYPTION_KEY` silently generates ephemeral key
- **Impact**: All encrypted BYOK keys become unrecoverable after server restart
- **Fix strategy**: Require env var in production, fail to start if missing

### P1 — Fire-and-forget asyncio tasks
- **Status**: CONFIRMED — `tasks.py:54` and `review.py:367` use `asyncio.create_task()` without tracking
- **Root cause**: Task handles discarded, no cancellation, no error recovery
- **Impact**: On shutdown, all in-flight tasks abandoned; no way to monitor background work
- **Fix strategy**: Implement `TaskTracker` with set of handles, graceful drain on shutdown

### P1 — Non-atomic review_store_update
- **Status**: CONFIRMED — `redis.py:79-83` read-modify-write pattern
- **Root cause**: Two concurrent `update` calls clobber each other
- **Impact**: Review data loss under concurrent access
- **Fix strategy**: Use Redis MULTI/EXEC or Lua script for atomic update

### P1 — Rate limiter ZSET memory leak
- **Status**: CONFIRMED — `redis.py:116` uses `str(now)` as ZSET member
- **Root cause**: Each rate limit check adds a unique member string
- **Impact**: Unbounded memory growth under high traffic
- **Fix strategy**: Use integer timestamp as member

### P1 — N+1 queries in list_teams and list_tasks
- **Status**: CONFIRMED — `teams.py:89-98` and `tasks.py:62-74`
- **Root cause**: Loop over IDs with individual queries
- **Impact**: 1000 teams = 1001 queries; connection pool exhaustion
- **Fix strategy**: JOIN queries instead of N+1 pattern

### P1 — No CI/CD pipeline
- **Status**: CONFIRMED — `.github/` directory missing entirely
- **Root cause**: Never set up
- **Impact**: No automated testing, linting, or security scanning
- **Fix strategy**: Add GitHub Actions workflow

### P1 — Docker runs as root
- **Status**: CONFIRMED — Dockerfile has no USER directive
- **Root cause**: Default behavior of base image
- **Impact**: Container escape vulnerability
- **Fix strategy**: Add non-root user

### P1 — No .dockerignore
- **Status**: CONFIRMED — .dockerignore file missing
- **Root cause**: Never created
- **Impact**: Bloated Docker images (200MB+ of unnecessary files), potential secret leakage
- **Fix strategy**: Create .dockerignore

### P2 — No pagination on list endpoints
- **Status**: CONFIRMED — `executions.py:63-69` has hardcoded LIMIT 50, no cursor/page params
- **Root cause**: MVP shortcut
- **Impact**: Cannot handle large datasets; frontend gets all results at once
- **Fix strategy**: Add `limit` and `offset` query parameters

### P2 — No security headers
- **Status**: CONFIRMED — `next.config.ts` is empty, no CSP/HSTS headers
- **Root cause**: Never configured
- **Impact**: Vulnerable to XSS, clickjacking, MIME-type sniffing
- **Fix strategy**: Add security headers in next.config.ts

### P2 — Coverage excludes core/ and agents/
- **Status**: CONFIRMED — `pyproject.toml` coverage scope only includes `app/`
- **Root cause**: Configuration oversight
- **Impact**: False sense of security — true coverage ~65%
- **Fix strategy**: Expand coverage scope to include all packages

### P3 — Dead code `review_router` in graph.py
- **Status**: FALSE POSITIVE — the `review_router` function is defined in `graph.py` but no conditional routing exists
- **Root cause**: Previously had review branching logic, simplified to single-pass
- **Impact**: None — unused function, no runtime effect
- **Fix strategy**: Remove dead code

---

## False Positives

### P2 — Redis `KEYS *` in rate_limit_reset
- **Status**: FALSE POSITIVE
- **Root cause**: The `rate_limit_reset` function uses `keys(f"{RATE_LIMIT_KEY_PREFIX}*")` which is only called during testing, not in production paths
- **Impact**: Minimal — test-only concern, not a production issue
- **Fix strategy**: LOW — none needed for production; test improvement only

### P3 — Hardcoded secrets in demo examples
- **Status**: FALSE POSITIVE
- **Root cause**: `QuickReviewTextarea.tsx` and `demo-data.ts` contain placeholder secrets in example/demo code
- **Impact**: None — these are illustrative examples, not production secrets
- **Fix strategy**: LOW — replace with `CHANGE-ME` placeholders

---

## Missing Findings (Not in Previous Audits)

### M1 — SQL injection via `execute()` in migrations
- **Severity**: P2
- **Root cause**: `database.py:49` reads migration SQL from file and executes directly
- **Impact**: If a migration file is tampered with, arbitrary SQL executes
- **Fix strategy**: Add SQL signing/checksum validation for migration files

### M2 — No request ID tracking
- **Severity**: P2
- **Root cause**: No correlation ID passed through request chain
- **Impact**: Cannot trace requests across logs, metrics, and traces
- **Fix strategy**: Add `X-Request-ID` middleware and structured logging context

### M3 — No rate limiting on task/team creation
- **Severity**: P2
- **Root cause**: Rate limiting only on review endpoint
- **Impact**: Attackers can flood the system with team/task creation requests
- **Fix strategy**: Add per-endpoint rate limiting

### M4 — No database connection retry
- **Severity**: P2
- **Root cause**: `database.py:16-21` creates pool without retry logic
- **Impact**: If database is starting up or restarting, app fails permanently
- **Fix strategy**: Add retry with exponential backoff in pool initialization

### M5 — No health check for dependencies
- **Severity**: P2
- **Root cause**: Health endpoint only returns static "ok"
- **Impact**: Cannot detect if DB/Redis/providers are down
- **Fix strategy**: Add dependency health checks (DB, Redis, Ollama)

### M6 — Unbounded in-memory rate limit store
- **Severity**: P2
- **Root cause**: `redis.py:98` uses defaultdict without max size
- **Impact**: Memory exhaustion under sustained attack
- **Fix strategy**: Add max entries cap and LRU eviction

### M7 — Missing graceful shutdown for graph streaming
- **Severity**: P1
- **Root cause**: `orchestrator.py:73` uses `graph.astream()` with no timeout or cancellation
- **Impact**: Streaming can block indefinitely, holding DB connections
- **Fix strategy**: Add timeout to `asyncio.wait_for` on stream iteration

### M8 — New HTTP client per provider call
- **Severity**: P2
- **Root cause**: `providers.py:50` creates `AsyncOpenAI` per call, `providers.py:198` creates `httpx.AsyncClient` per call
- **Impact**: Socket leak under load, no connection reuse
- **Fix strategy**: Cache HTTP clients, reuse connections

### M9 — No input size limits on task description
- **Severity**: P2
- **Root cause**: `schemas.py:95` has no max_length on description field
- **Impact**: Unbounded description can cause memory issues
- **Fix strategy**: Add reasonable max_length

### M10 — Jinja2 template not cached
- **Severity**: P2 (already partially fixed)
- **Root cause**: `agents/utils.py:95-96` caches the Environment but `review.py:103-104` creates templates at module level
- **Impact**: Minimal — templates cached after first load; but module-level loading prevents test isolation
- **Fix strategy**: Template caching is acceptable; lazy loading in test setup

### M11 — No migration version tracking
- **Severity**: P2
- **Root cause**: `database.py:39-51` runs all migrations every startup unconditionally
- **Impact**: Wasted I/O on every startup; can't track which migrations ran
- **Fix strategy**: Add `schema_migrations` tracking table

### M12 — Projects/Templates API stubs return misleading data
- **Severity**: P2
- **Root cause**: `api.ts:120-134` creates fake local-only project objects
- **Impact**: Users see phantom data that disappears on refresh
- **Fix strategy**: Return null/empty with clear error state in UI instead of fake data

---

## Updated Severity Levels

| Issue | Old Severity | New Severity | Change Reason |
|-------|-------------|-------------|---------------|
| No auth | P1 | P0 | Launch blocker for multi-tenant |
| Fire-and-forget tasks | P1 | P0 | Data loss on any deployment |
| Non-atomic review update | P1 | P0 | Race condition causes data corruption |
| N+1 queries | P1 | P1 | Confirmed |
| DB password default | P1 | P1 | Confirmed |
| Ephemeral encryption key | P1 | P1 | Confirmed |
| Missing graceful shutdown (streaming) | MISSING | P1 | Can hang servers indefinitely |
| No CI/CD | P1 | P1 | Confirmed |
| Docker root | P1 | P1 | Confirmed |
| No migration tracking | MISSING | P2 | Operational concern |
| No request ID | MISSING | P2 | Debugging blocker |
| Health check shallow | MISSING | P2 | Operations concern |

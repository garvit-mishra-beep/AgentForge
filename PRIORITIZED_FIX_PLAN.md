# Prioritized Fix Plan — AgentForge

> Effort estimates: hours (h), days (d), weeks (w)

---

## P0 — Launch Blockers (0 remaining, 2 fixed)

| # | Issue | Fix | Effort | Status |
|---|-------|-----|--------|--------|
| ~~P0-1~~ | `_utcnow()` returns local time, not UTC | `datetime.now(timezone.utc)` | 5m | ✅ Fixed |
| ~~P0-2~~ | Timeout detection via `"timeout" in result.content` | `_is_timeout()` with sentinel attribute | 15m | ✅ Fixed |

---

## P1 — Serious Production Risks (14 items)

| # | Issue | File | Fix | Effort | Impact |
|---|-------|------|-----|--------|--------|
| P1-1 | **No authentication** — hardcoded demo user across ALL routes | All routes | Add JWT middleware + user registration | 3-5d | 🔴 Auth |
| P1-2 | **No task tracking** — `create_task` handles discarded | `routes/*.py`, `orchestrator.py` | Track tasks in a set; cancel on shutdown | 4h | 🔴 Reliability |
| P1-3 | **Orchestrator streaming has no timeout** | `orchestrator.py` | Add `asyncio.wait_for` around `graph.astream()` | 1h | 🔴 Reliability |
| P1-4 | **`review_store_update` non-atomic** | `core/redis.py` | Use Redis MULTI/EXEC; add in-memory lock | 2h | 🔴 Data integrity |
| P1-5 | **Redis operations not wrapped for mid-operation fallback** | `core/redis.py` | Try/except all Redis calls → fallback to in-memory | 2h | 🔴 Reliability |
| P1-6 | **Encryption key not required** | `core/encryption.py` | Validate key presence at startup; fail if missing | 1h | 🔴 Security |
| P1-7 | **DB password in config default** | `core/config.py` | Remove default; validate at startup | 30m | 🔴 Security |
| P1-8 | **N+1 queries in list_teams/list_tasks** | `routes/teams.py`, `routes/tasks.py` | Use JOIN queries | 3h | 🟠 Performance |
| P1-9 | **Dockerfile runs as root, no .dockerignore** | `Dockerfile` | Add non-root user, .dockerignore | 1h | 🟠 Security |
| P1-10 | **No CI/CD** | Missing `.github/` | Add GitHub Actions: lint + test + build | 4h | 🟠 DevEx |
| P1-11 | **No rate limiting on team/task creation** | `routes/teams.py`, `routes/tasks.py` | Add rate limit check middleware | 2h | 🟠 Abuse |
| P1-12 | **Frontend silences API errors with stubs** | `lib/api.ts` | Remove catch-all stubs; show error UI | 2h | 🟠 UX |
| P1-13 | **Coverage excludes core/ and agents/** | `pyproject.toml` | Change `source = ["app"]` to `source = [". "]` or add paths | 5m | 🟠 Testing |
| P1-14 | **No graceful shutdown for in-flight tasks** | `app/main.py` | Add task drain in lifespan shutdown | 3h | 🟠 Reliability |

---

## P2 — Technical Debt (12 items)

| # | Issue | File | Fix | Effort |
|---|-------|------|-----|--------|
| P2-1 | `load_prompt_template` creates new Environment per call | `agents/utils.py` | Cache Environment at module level | 30m |
| P2-2 | New HTTP client per provider call | `core/providers.py` | Use shared httpx client; connection pooling | 1h |
| P2-3 | Ollama default timeout (300s) too high | `core/providers.py` | Reduce to 60s (matches pipeline max) | 5m |
| P2-4 | Dead code: `review_router` function | `agents/graph.py` | Remove unused function | 5m |
| P2-5 | Rate limiter uses `str(now)` as ZSET member | `core/redis.py` | Use integer timestamp (second precision) | 1h |
| P2-6 | `rate_limit_reset()` uses `KEYS *` | `core/redis.py` | Track rate limit keys in a separate set | 1h |
| P2-7 | In-memory stores have no size cap | `core/redis.py` | Add max-size eviction (LRU) | 2h |
| P2-8 | Hardcoded secret in example code | `QuickReviewTextarea.tsx` | Replace with `"CHANGE-ME"` | 5m |
| P2-9 | `next.config.ts` is empty — no security headers | `next.config.ts` | Add CSP, HSTS, X-Frame-Options | 30m |
| P2-10 | Frontend hydration mismatch on landing page | `app/page.tsx` | Add loading skeleton; consistent server data | 2h |
| P2-11 | Model routing by keyword is fragile | `core/providers.py` | Use explicit model→provider mapping | 2h |
| P2-12 | `pyproject.toml` coverage scope too narrow | `pyproject.toml` | Expand to cover core/ and agents/ | 5m |

---

## P3 — Polish (3 items)

| # | Issue | File | Fix | Effort |
|---|-------|------|-----|--------|
| P3-1 | Demo data has hardcoded secret | `demo-data.ts` | Replace with `"${SECRET_KEY}"` placeholder | 5m |
| P3-2 | Observability is single log line | `core/observability.py` | Add Prometheus counters/histograms | 4h |
| P3-3 | `review_models_*` env vars parsed every registry init | `core/model_registry.py` | Parse once, cache result | 15m |

---

## Roadmap: 8/10 → 9/10 → 10/10

### Phase 1 (Week 1): Security & Auth — from 7.5 → 8.5
```
P1-1  Auth middleware          ████████████ 3-5d
P1-6  Encryption key required  ██           1h
P1-7  DB password validation   █            30m
P1-9  Docker security          ██           1h
P1-12 Error handling fix       ██           2h
P2-9  Security headers         █            30m
```
**Impact**: System becomes deployable with basic security.

### Phase 2 (Week 2): Reliability — from 8.5 → 9.0
```
P1-2  Task tracking            ████          4h
P1-3  Stream timeout           █             1h
P1-4  Atomic review update     ██            2h
P1-5  Redis failover           ██            2h
P1-14 Graceful shutdown        ███           3h
P2-1  Template caching         █             30m
P2-5  Rate limiter fix         █             1h
```
**Impact**: Reviews survive restarts, no lost tasks, proper timeouts.

### Phase 3 (Week 3): Performance & Scale — from 9.0 → 9.5
```
P1-8  N+1 query fix            ███           3h
P1-11 Rate limit creation      ██            2h
P2-2  HTTP client pooling      █             1h
P2-3  Ollama timeout fix       █             5m
P2-6  KEYS * replacement       █             1h
P2-7  Memory caps              ██            2h
P2-11 Model routing fix        ██            2h
```
**Impact**: Handles 100+ concurrent users, no memory leaks.

### Phase 4 (Week 4): Testing & CI — from 9.5 → 10.0
```
P1-10 CI/CD pipeline           ████          4h
P1-13 Coverage fix             █             5m
P2-12 Coverage expansion       █             5m
+ 20 new tests (integration, failure, load)
+ Frontend component tests
```
**Impact**: Full test coverage, automated CI, deployment confidence.

---

## Effort Summary

| Phase | Effort | Score Gain |
|-------|--------|------------|
| Phase 1: Security | ~10 days | 7.5 → 8.5 |
| Phase 2: Reliability | ~5 days | 8.5 → 9.0 |
| Phase 3: Performance | ~4 days | 9.0 → 9.5 |
| Phase 4: Testing | ~3 days | 9.5 → 10.0 |
| **Total** | **~22 days** | **7.5 → 10.0** |

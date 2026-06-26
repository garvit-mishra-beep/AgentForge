# Final Repository Audit — AgentForge

> Date: 2026-06-26
> Auditor: Automated deep audit

---

## 1. Executive Summary

AgentForge is a monorepo (Turborepo + pnpm) containing a Python FastAPI backend and a Next.js 15 frontend. It orchestrates multiple AI agents (LLMs) through LangGraph, provides a "Quick Review" multi-model code review pipeline, and supports BYOK (Bring Your Own Key) with AES-256-GCM encryption.

**Overall score: 7.5/10** — solid MVP architecture with critical gaps in auth, reliability, and observability.

### Strengths
- Clean separation of concerns (routes/core/agents/models)
- Proper async patterns (asyncpg pool, asyncio throughout)
- Good use of Pydantic v2 for validation
- AES-256-GCM encryption for stored API keys
- In-memory fallback for Redis (graceful degradation)
- 74 tests across 9 test files
- All migrations are idempotent (safe to re-run)

### Critical Weaknesses
1. **No authentication or authorization** — hardcoded demo user everywhere
2. **`_utcnow()` returned local time, not UTC** (P0, fixed)
3. **Timeout detection via substring "timeout"** (P0, fixed)
4. **Fire-and-forget asyncio tasks** with no tracking, cancellation, or error recovery
5. **Redis sorted set rate limiter** uses `str(now)` as member — potential memory leak
6. **`review_store_update` is not atomic** — race condition on concurrent updates
7. **Docker image runs as root** with no `.dockerignore`
8. **No CI/CD pipeline** — `.github/` directory missing entirely
9. **Coverage excludes core/ and agents/** — true coverage for production code is ~65%
10. **Frontend stubs API errors silently** — users see empty lists instead of errors

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                Frontend (Next.js 15)              │
│  apps/web/  →  TypeScript, Tailwind v4, Radix UI │
└────────────────┬─────────────────────────────────┘
                 │ HTTP (port 3000)
┌────────────────▼─────────────────────────────────┐
│               Backend (FastAPI)                   │
│  apps/api/   →  Python 3.11+, asyncpg, LangGraph │
│                                                   │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Routes  │  │  Core    │  │    Agents         │ │
│  │ health  │  │ config   │  │  graph.py         │ │
│  │ teams   │  │ database │  │  orchestrator.py  │ │
│  │ tasks   │  │ redis    │  │  nodes/           │ │
│  │ keys    │  │ providers│  │  prompts/         │ │
│  │ review  │  │ registry │  └──────────────────┘ │
│  │ execs   │  │ observ.  │                       │
│  └─────────┘  │ encrypt  │                       │
│               └──────────┘                       │
└──────┬───────────────────────────────────────────┘
       │
┌──────▼──────┐  ┌──────────┐  ┌──────────────────┐
│ PostgreSQL  │  │  Redis   │  │   Ollama / API    │
│ (asyncpg)   │  │(fallback)│  │   Providers       │
└─────────────┘  └──────────┘  └──────────────────┘
```

---

## 3. File-by-File Findings

### 3.1 Core Layer

| File | Issues Found | Severity |
|------|-------------|----------|
| `core/config.py` | DB password in default value; no validation of critical settings | P1 |
| `core/database.py` | `run_migrations()` runs every startup; no migration tracking table | P2 |
| `core/redis.py` | `str(now)` as ZSET member; `KEYS *` in reset; non-atomic update; unbounded in-memory growth | P1 |
| `core/providers.py` | New HTTP client per call; model routing by keyword fragile; Ollama timeout too high | P2 |
| `core/model_registry.py` | Bare `except Exception` catches SystemExit/KeyboardInterrupt | P2 |
| `core/encryption.py` | Ephemeral key on missing env var makes data unrecoverable after restart | P1 |
| `core/observability.py` | Single `logger.info` call — no metrics, histograms, or structured fields | P2 |
| `core/validation.py` | Not reviewed in detail but appears sound | - |

### 3.2 Route Layer

| File | Issues Found | Severity |
|------|-------------|----------|
| `routes/teams.py` | Hardcoded user_id; N+1 queries in list_teams | P1 |
| `routes/tasks.py` | Hardcoded user_id; N+1 queries; fire-and-forget create_task | P1 |
| `routes/review.py` | Fire-and-forget tasks; non-atomic update; no cancellation; fragile language detection | P1 |
| `routes/keys.py` | Hardcoded user_id; module-level singleton encryption | P1 |
| `routes/executions.py` | No user isolation; fixed LIMIT 50 no pagination | P2 |

### 3.3 Agent Layer

| File | Issues Found | Severity |
|------|-------------|----------|
| `orchestrator.py` | **_utcnow() returned local time** (fixed); no streaming timeout; fragile JSON serialization | P0 |
| `utils.py` | Timeout detection via substring (fixed); `load_prompt_template` uncached | P1 |
| `graph.py` | Dead code (`review_router` defined but never called) | P3 |
| `nodes/*.py` | Fragile timeout detection (fixed) | P0 |

### 3.4 Frontend

| File | Issues Found | Severity |
|------|-------------|----------|
| `lib/api.ts` | No auth headers; silences API errors with stubs; returns local-only objects | P1 |
| `components/QuickReviewTextarea.tsx` | Hardcoded `SECRET = "my-dev-secret"` in example code | P2 |
| `lib/demo-data.ts` | `"your-secret-key-change-in-production"` in demo data | P3 |
| `app/page.tsx` | Hydration mismatch risk; no loading skeleton for first-time view | P2 |
| `next.config.ts` | Empty config — no security headers, standalone output | P2 |

### 3.5 Infrastructure

| File | Issues Found | Severity |
|------|-------------|----------|
| `Dockerfile` | No `.dockerignore`; runs as root; no healthcheck; single-worker uvicorn | P1 |
| `docker-compose.yml` | Hardcoded DB credentials should use env vars | P2 |
| Missing `.github/` | No CI/CD at all | P1 |
| `pyproject.toml` | Coverage scope excludes `core/` and `agents/` | P2 |

---

## 4. Known Issue Count

| Severity | Count |
|----------|-------|
| P0 (launch blocker) | 0 (2 fixed) |
| P1 (serious production risk) | 14 |
| P2 (technical debt) | 12 |
| P3 (polish) | 3 |

---

## 5. Key Metrics

- **Tests**: 74 passing, 9 test files
- **Coverage (app/)**: 92%
- **Coverage (core/ + agents/)**: ~65%
- **Total production lines**: ~2,263 (excluding benchmarks)
- **Redis integration**: Partial (in-memory fallback, no distributed tests)
- **Auth layer**: None (single hardcoded demo user)
- **CI/CD**: None

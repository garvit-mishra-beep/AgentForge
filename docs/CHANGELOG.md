# Changelog — AgentForge

**Format:** [Keep a Changelog](https://keepachangelog.com/)
**Versioning:** [Semantic Versioning](https://semver.org/)

---

## Unreleased

### Added
- All 6 agent roles (Team Lead, Backend, Frontend, QA, Security, DevOps)
- Agent long-term memory with pgvector semantic search
- Token cost tracking per task step
- Human-in-the-loop approval gates in WebSocket protocol
- Human-in-the-loop interrupt/resume flow

### Fixed
- LangGraph execution timeout enforcement (MAX_STEPS=20)
- WebSocket ping/pong keepalive (30s interval)
- Task output persistence on agent error mid-step
- Redis JWT cache TTL (1 hour default)

---

## v0.3.0 — Real-Time Streaming & Task History

**Released:** 2026-06-15

### Added
- WebSocket real-time agent output streaming
- Agent message chunk streaming (token-level in output panel)
- Task history page with filtering (by project, status, date)
- Task detail view with step-by-step breakdown
- Output panel with file listing and download
- `outputs` table in PostgreSQL for generated files
- Auto-scroll and collapse for long agent outputs

### Changed
- Agent execution events now publish to Redis pub/sub instead of direct WebSocket
- Task status transitions logged in `task_steps` table
- Frontend WebSocket client with auto-reconnect (exponential backoff)

### Fixed
- Task creation failing when team has no agents assigned
- Agent message order not preserved in history view
- Memory leak in WebSocket connection pool

---

## v0.2.0 — LangGraph Agent Execution

**Released:** 2026-06-01

### Added
- LangGraph agent execution graph (3 roles: Team Lead, Backend Engineer, Reviewer)
- Backend Engineer node with Claude Sonnet integration
- Reviewer node with GPT-4o integration
- Conditional routing (review feedback → backend revision cycle)
- Agent output validation pipeline (schema → file path → import → syntax check)
- `task_steps` and `messages` tables in PostgreSQL
- Confidence score system with retry logic
- Hallucination guard: output validation with rejection logging

### Changed
- Migrated from linear agent loop to LangGraph StateGraph
- Task execution now async with progress tracking

### Fixed
- Agent retry not decrementing on valid-but-low-confidence outputs

---

## v0.1.0 — Monorepo Scaffold & Foundation

**Released:** 2026-05-20

### Added
- Turborepo monorepo setup (apps/web, apps/api, packages/db, packages/types, packages/ui)
- Next.js 15 App Router frontend with Tailwind CSS
- FastAPI backend with asyncpg and Redis integration
- Clerk authentication (email/password, Google OAuth, GitHub OAuth)
- Project CRUD (create, list, get, update, delete)
- Team CRUD with agent role-to-model assignment
- PostgreSQL schema (users, projects, teams, agents, tasks)
- Prisma ORM with initial migrations
- Docker Compose setup (PostgreSQL 16 + Redis 7)
- Basic dashboard page with project list
- Team builder page (static, no drag-and-drop yet)
- API documentation (auto-generated OpenAPI at /docs)
- CI/CD pipeline (GitHub Actions: lint → test → deploy)
- Vercel + Railway deployment configurations
- `CONTRIBUTING.md`, `SETUP.md`, `ENV.md`, `CLAUD.md`
- Architecture Decision Records (ADR-001 through ADR-008)

### Notes
- Agent execution was still linear (no LangGraph) in this release
- Only 3 agent roles existed (Team Lead, Backend, Reviewer)
- No WebSocket support — task results were polled via REST
- No agent memory or vector search

# Project Context — AgentForge

**Last Updated:** June 25, 2026

---

## Current Project State

### Done

- Monorepo scaffold with Turborepo (apps/web, apps/api, packages/db, packages/types, packages/ui)
- Clerk authentication (email/password, Google OAuth, GitHub OAuth)
- Project CRUD (create, list, get, update, delete)
- Team CRUD with agent role-to-model assignment
- LangGraph agent execution graph (3 roles: Team Lead, Backend Engineer, Reviewer)
- Basic task creation and execution pipeline
- WebSocket real-time streaming of agent outputs
- Task history page with basic filtering
- Docker Compose setup (PostgreSQL 16 + Redis 7)
- Prisma schema and initial migrations
- API documentation (auto-generated OpenAPI)

### In Progress

- Agent long-term memory with pgvector (semantic search across past task outputs)
- All 6 agent roles with production system prompts (Team Lead, Backend, Frontend, QA, Security, DevOps)
- Token cost tracking per task step
- Human-in-the-loop approval gates in the LangGraph workflow
- Output panel with file diff viewer (syntax-highlighted diff between file versions)
- Task execution timeout enforcement (MAX_STEPS safeguard)

### Blocked

- **Parallel agent execution** — Waiting on LangGraph v0.3+ for branch-and-merge parallelism support
- **Team templates** — Needs design sign-off on template schema before implementation
- **Model marketplace UI** — Backend API is ready, frontend design is not finalized

---

## Active Sprint Goals (Sprint 6)

1. Ship all 6 agent roles with v1.0 system prompts and full test coverage
2. Implement pgvector memory retrieval in the Team Lead node (inject top-3 relevant past tasks)
3. Add token cost tracking and display in the task detail view
4. Implement human-in-the-loop interrupt/resume flow in the WebSocket protocol
5. Reach 80% test coverage on agent orchestration layer

---

## Known Issues

| ID | Summary | Severity | Status |
|----|---------|----------|--------|
| P0-001 | No timeout enforcement on LangGraph execution — tasks can run indefinitely | Critical | Fix in progress |
| P0-002 | WebSocket silently drops after 5 minutes idle — no ping/pong keepalive | Critical | Assigned |
| P0-003 | Task output not persisted on agent error mid-step | Critical | Fix in progress |
| P1-004 | Role assignment UI breaks for teams with >4 members | High | Triaged |
| P1-005 | Redis JWT cache keys have no TTL — memory leak under load | High | Assigned |
| P1-006 | Model selector saves without validating API key | High | Open |

See full list in [BUGS.md](BUGS.md)

---

## Recent Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-20 | Adopt pgvector over standalone vector DB (Pinecone/Qdrant) | Single database, simpler ops, sufficient for current scale |
| 2026-06-18 | System prompts stored as Jinja2 templates, not in DB | Version-controlled, testable, reviewable in PRs |
| 2026-06-15 | WebSocket protocol uses JSON event envelopes (not raw text/SSE) | Structured events enable typed dispatchers on both FE and BE |
| 2026-06-10 | Free tier limited to GPT-4o-mini and Claude Haiku only | Cost control; premium models reserved for paid tiers |
| 2026-06-05 | Agent memories pruned at 180 days or 10k entries per agent, whichever hits first | Prevents vector index bloat while retaining useful context |

---

## Next 3 Priorities

1. **Ship P0 fixes** — Timeout enforcement, WebSocket keepalive, error-safe persistence
2. **Release v0.4.0** — All 6 roles + agent memory + cost tracking
3. **Open-source the monorepo** — Clean up TODOs, add CONTRIBUTING.md, publish to GitHub

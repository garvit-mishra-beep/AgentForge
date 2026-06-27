# Roadmap — AgentForge

**Last Updated:** June 2026

---

## Milestones

| Version | Target Date | Theme | Status |
|---------|-------------|-------|--------|
| MVP (v0.1 – v0.3) | June 2026 | Foundation | ✅ Released |
| V1.0 | August 2026 | Production-ready | 🔄 In progress |
| V1.5 | November 2026 | Scale | 📅 Planned |
| V2.0 | Q1 2027 | Enterprise | 📅 Planned |

---

## MVP (v0.1 – v0.3) — Foundation

**Status:** ✅ Released

### In Scope
- Monorepo scaffold (Turborepo + pnpm workspaces)
- Clerk authentication (email/password, Google, GitHub OAuth)
- Project CRUD
- Team CRUD with role-to-model assignment
- LangGraph agent execution graph (3 roles: Lead, Backend, Reviewer)
- Real-time WebSocket agent streaming
- Basic output panel with file listing
- Task history with filtering
- Docker Compose (PostgreSQL + Redis)
- Prisma schema + migrations
- CI/CD (GitHub Actions → Vercel + Railway)
- Documentation (README, SETUP, ENV, API, CLAUDE, CONTRIBUTING)

### Out of Scope
- All 6 roles (only 3 shipped)
- Agent memory (pgvector)
- Token cost tracking
- Human-in-the-loop approval gates
- Model marketplace UI
- Team templates

---

## V1.0 — Production-Ready

**Target:** August 2026
**Status:** 🔄 In Progress

### In Scope
- All 6 agent roles with v1.0 system prompts
- Production-grade system prompts (chain-of-thought, self-review, structured output)
- Agent long-term memory with pgvector semantic search
- Token cost tracking per task, per project, per model
- Human-in-the-loop approval gates in WebSocket protocol
- Task timeout enforcement (MAX_STEPS safeguard)
- WebSocket ping/pong keepalive
- Secure API key storage (encrypted at rest)
- PostgreSQL connection pooling
- 80%+ test coverage on agent orchestration layer
- Output panel with file diff viewer (syntax-highlighted)
- Error handling: consistent error response format
- Retry logic with exponential backoff for AI provider calls
- Circuit breaker for AI provider failures
- Loading states for task execution view
- Free/Pro/Team pricing tiers enforcement

### Out of Scope
- Parallel agent execution
- Team templates
- Model marketplace UI
- Enterprise SSO (SAML)
- On-premise deployment
- Audit logs

---

## V1.5 — Scale

**Target:** November 2026
**Status:** 📅 Planned

### In Scope
- **Parallel agent execution** — Multiple agents working simultaneously (requires LangGraph branch-and-merge)
- **Team templates** — Pre-built role-to-model assignments ("Full Stack", "Backend Heavy", "Security Focused")
- **Model marketplace UI** — Browse models by capability, cost, and speed; one-click assignment
- **Task history search** — Full-text + semantic search over past task outputs
- **File upload support** — Attach a codebase zip for richer agent context
- **Project-level agent memory sharing** — All agents on a project share memory across teams
- **Performance optimizations** — Cached prompt rendering, Redis pipeline batching
- **Usage dashboard** — Per-project, per-model, per-task cost breakdown with charts

### Out of Scope
- Custom model endpoint support
- On-premise deployment
- Enterprise SSO

---

## V2.0 — Enterprise

**Target:** Q1 2027
**Status:** 📅 Planned

### In Scope
- **Enterprise SSO (SAML/SCIM)** — Okta, Azure AD, Google Workspace integration
- **Audit logs** — Immutable log of all task executions, agent decisions, and human approvals for SOC2 compliance
- **On-premise Docker deployment** — Full stack deployable in customer's infrastructure (Kubernetes helm chart)
- **Custom model endpoints** — Bring your own model (OpenAI-compatible API endpoint)
- **API for external integration** — Create tasks, query history, manage teams via REST API
- **Agent performance scoring** — Track agent accuracy, speed, and cost over time; compare models

### Out of Scope
- AI model training or fine-tuning
- Native IDE plugin (VS Code extension)
- Multi-user real-time collaboration on the same task
- Agent-to-agent voice communication

---

## Future Concepts (Post-V2.0)

- **AI workforce analytics dashboard** — Cross-project agent performance metrics, bottleneck identification, cost optimization recommendations
- **Cross-team agent coordination** — Agents from different projects collaborating on shared tasks
- **Human-AI hybrid teams** — Human developers working alongside AI agents in the same task, with human-in-the-loop at every step
- **Agent performance scoring** — Automated evaluation of agent outputs against acceptance criteria, model comparison, regression detection

---

## Feature Requests

If you'd like to suggest a feature, please open a GitHub issue with the "feature request" template. We prioritize based on:
1. User demand (number of +1s)
2. Alignment with product vision
3. Engineering effort vs. impact
4. Paid tier requirements (Enterprise features must support SSO and audit)

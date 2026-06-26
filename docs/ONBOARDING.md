# Onboarding Guide — AgentForge

**Welcome! This guide will help you get productive in your first week.**

---

## Repo Tour

```
agentforge/
├── apps/
│   ├── web/                 # Next.js 15 frontend
│   │   ├── app/             # App Router (pages, layouts, API routes)
│   │   │   ├── dashboard/   → Start here: project list page
│   │   │   ├── team-builder/→ Drag-and-drop role assignment
│   │   │   ├── tasks/[id]/  → Main workspace (agent streaming, output panel)
│   │   │   └── history/     → Searchable past tasks
│   │   └── components/      → Reusable UI components
│   │
│   └── api/                 # FastAPI backend
│       ├── app/routes/      → REST endpoints (projects, teams, tasks, auth)
│       ├── app/ws/          → WebSocket handlers (task streaming)
│       ├── agents/          → THE CORE: LangGraph graph + agent nodes
│       │   ├── graph.py     → StateGraph definition
│       │   ├── nodes/       → Agent node implementations
│       │   └── prompts/     → Jinja2 system prompt templates
│       └── core/            → Config, auth, database, redis, model registry
│
├── packages/
│   ├── db/                  → Prisma schema + migrations
│   ├── types/               → Shared TypeScript types
│   └── ui/                  → Shared React components
│
├── docker-compose.yml
├── turbo.json
└── package.json
```

**Key insight:** The agent orchestration code lives in `apps/api/agents/`. If you're working on agent behavior, start there. If you're working on the UI, start in `apps/web/`.

---

## First Task Suggestions by Area

### Frontend: "Add a component to the output panel"

1. Learn the component patterns in `apps/web/components/`
2. Create `apps/web/components/agents/FileDiff.tsx` — a syntax-highlighted diff viewer
3. Wire it into `apps/web/app/tasks/[id]/page.tsx` as a tab in the output panel
4. Test with `pnpm test:web`

### Backend: "Add an endpoint to list completed tasks"

1. Study `apps/api/app/routes/tasks.py` for existing patterns
2. Add `GET /api/v1/tasks/completed` with optional `project_id` filter
3. Define Pydantic models if needed
4. Add tests in `apps/api/tests/test_routes/test_tasks.py`

### Agent: "Add a new agent role"

1. Read `docs/AGENT_ROLES.md` and `docs/AGENT_PROMPTS.md` to understand the pattern
2. Create the system prompt template in `apps/api/agents/prompts/`
3. Create the node implementation in `apps/api/agents/nodes/`
4. Register the node in `apps/api/agents/graph.py`
5. Add tests with mocked AI provider calls

### Infra: "Improve CI caching"

1. Study `.github/workflows/deploy.yml`
2. Add pnpm store caching step
3. Add Playwright browser caching step
4. Verify cache hit reduces CI time by 40%+

---

## Ownership Map

| Area | Primary Owner | Files |
|------|--------------|-------|
| Agent orchestration (LangGraph) | Backend team | `apps/api/agents/*` |
| Agent prompts and templates | Backend + Docs | `apps/api/agents/prompts/*` |
| REST API endpoints | Backend | `apps/api/app/routes/*` |
| WebSocket protocol | Backend | `apps/api/app/ws/*` |
| Database schema | Backend | `packages/db/schema.prisma` |
| Frontend pages and routing | Frontend | `apps/web/app/*` |
| UI components | Frontend | `apps/web/components/*` |
| Shared component library | Frontend | `packages/ui/*` |
| CI/CD and deployment | DevOps | `.github/*`, `Dockerfile` |
| Documentation | Docs | `docs/*` |

---

## Key Concepts to Understand Before Touching Agent Code

### 1. LangGraph State

The `AgentState` TypedDict is passed between every agent node. You must understand what fields exist, which ones each node reads and writes, and how state flows through the graph.

Read: `apps/api/agents/graph.py` and `docs/TECH_SPEC.md#langgraph-agent-graph`

### 2. Handoff Protocol

When one agent finishes, its output is stored in `state.agent_outputs[role]`. The next agent reads from this dictionary. The handoff is not automatic — the graph's edges must be correctly defined to route to the next node.

Read: `docs/AGENT_ROLES.md#handoff-protocol` for each role

### 3. Prompt Versioning

System prompts are Jinja2 templates in `apps/api/agents/prompts/`. Each template has a version header (`# v1.0`). When you modify a prompt, you MUST bump the version. This allows us to trace which prompt version was used for which task.

### 4. Model Registry

Do not hardcode model names. Use `model_registry.py` to look up models by ID. Validate that a model supports the required context length for the role.

Read: `docs/MODEL_REGISTRY.md`

---

## Common First-Week Mistakes

| Mistake | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| Modifying prompt template without bumping version | Not knowing the convention | Read `docs/CONVENTIONS.md` first |
| Forgetting to run `pnpm db:migrate` after schema change | Not understanding Prisma workflow | Add migration step to your PR checklist |
| Hardcoding model names in node code | Copying patterns from single-model projects | Always use `model_registry.get_model()` |
| Writing tests without mocking AI providers | Tests call real APIs, hit rate limits | Use `pytest-httpx` fixture from `tests/conftest.py` |
| Not checking LangGraph state field existence | Assuming fields exist in TypedDict | Check `AgentState` definition in `graph.py` |
| Adding JSX without `"use client"` directive | Next.js 15 server component by default | Add `"use client"` for any component with state, effects, or event handlers |
| Committing `.env` files with real secrets | Gitignore misconfiguration | Check `.gitignore`; use `.env.example` for reference |
| Creating agent node without updating `graph.py` | Forgetting to register | Follow the recipe in `docs/CLAUDE.md#add-a-new-agent-role` |

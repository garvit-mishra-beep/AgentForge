# Folder Structure — AgentForge MVP

---

## Top Level

```
agentforge/
├── apps/
│   ├── web/                    # Next.js 15 Frontend (TypeScript)
│   └── api/                    # FastAPI Backend (Python)
├── docker-compose.yml          # PostgreSQL for local dev
├── turbo.json                  # Turborepo pipeline config
├── package.json                # Workspace root (pnpm)
├── pnpm-workspace.yaml         # pnpm workspace definition
├── tsconfig.json               # Shared TS config base
├── .gitignore
├── .prettierrc
└── README.md
```

---

## Frontend — `apps/web/`

```
apps/web/
├── app/
│   ├── layout.tsx              # Root layout with fonts, metadata
│   ├── page.tsx                # Dashboard — list teams, recent tasks
│   ├── teams/
│   │   ├── page.tsx            # Team list page
│   │   ├── new/
│   │   │   └── page.tsx        # Create team form
│   │   └── [id]/
│   │       └── page.tsx        # Team detail — view members, create task
│   ├── tasks/
│   │   ├── page.tsx            # Task history list
│   │   └── [id]/
│   │       └── page.tsx        # Task execution view — live timeline
│   └── globals.css             # Tailwind imports
├── components/
│   ├── ui/                     # Primitive UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── badge.tsx
│   │   └── skeleton.tsx
│   ├── TeamForm.tsx            # Create/edit team form
│   ├── TeamCard.tsx            # Team summary card
│   ├── TeamMemberSelect.tsx    # Model picker per role
│   ├── TaskForm.tsx            # Create task form
│   ├── TaskCard.tsx            # Task summary card
│   ├── ExecutionTimeline.tsx   # Step-by-step execution display
│   ├── AgentMessage.tsx        # Single agent output bubble
│   ├── TaskStatusBadge.tsx     # Color-coded status indicator
│   └── EmptyState.tsx          # "No items yet" placeholder
├── lib/
│   └── api.ts                  # Typed fetch wrapper for all API calls
├── types/
│   └── index.ts                # TypeScript type definitions
├── next.config.ts              # Next.js configuration
├── tailwind.config.ts          # Tailwind theme
├── postcss.config.js           # PostCSS config
├── tsconfig.json               # TypeScript config
└── package.json
```

---

## Backend — `apps/api/`

```
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory, middleware, startup
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health — health check endpoint
│   │   ├── teams.py            # Team CRUD routes
│   │   └── tasks.py            # Task create, list, detail, messages
├── agents/
│   ├── __init__.py
│   ├── graph.py                # LangGraph StateGraph definition
│   ├── orchestrator.py         # High-level orchestrator — runs graph in background
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── team_lead_node.py   # Planning node
│   │   ├── builder_node.py     # Implementation node
│   │   └── reviewer_node.py    # Review node
│   └── prompts/
│       ├── team_lead.jinja2    # Team Lead system prompt template
│       ├── builder.jinja2      # Builder system prompt template
│       └── reviewer.jinja2     # Reviewer system prompt template
├── core/
│   ├── __init__.py
│   ├── config.py               # Settings from environment variables
│   ├── database.py             # asyncpg connection pool
│   └── providers.py            # AI provider clients (OpenAI, Anthropic, Google)
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic request/response models
├── migrations/
│   └── 001_initial.sql         # Initial database schema
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Production container image
├── .dockerignore
└── pyproject.toml              # Python project config (ruff, pytest)
```

---

## Database — PostgreSQL

```
┌─────────────┐       ┌─────────────────────┐
│    users    │       │       teams          │
│─────────────│       │─────────────────────│
│ id (PK)     │──┐    │ id (PK)              │
│ email (UQ)  │  │    │ name                 │
│ name        │  │    │ description          │
│ created_at  │  └───│ created_by (FK→users) │
└─────────────┘       │ created_at           │
                      │ updated_at           │
                      └──────────┬───────────┘
                                 │
                      ┌──────────┴───────────┐
                      │    team_members      │
                      │─────────────────────│
                      │ id (PK)              │
                      │ team_id (FK→teams)   │
                      │ role (ENUM)          │
                      │ model (VARCHAR)      │
                      │ created_at           │
                      │ UQ: (team_id, role)  │
                      └─────────────────────┘

┌──────────────────┐
│      tasks       │
│──────────────────│
│ id (PK)          │
│ team_id (FK)     │──┘
│ title            │
│ description      │
│ status (ENUM)    │
│ created_by (FK)  │──┘
│ created_at       │
│ updated_at       │
│ completed_at     │
│ error_message    │
└────────┬─────────┘
         │
┌────────┴─────────┐      ┌──────────────────┐
│   task_messages  │      │   executions     │
│──────────────────│      │──────────────────│
│ id (PK)          │      │ id (PK)          │
│ task_id (FK)     │      │ task_id (FK/UQ)  │
│ step_order (INT) │      │ status (ENUM)    │
│ role (ENUM)      │      │ graph_state(JSON)│
│ model (VARCHAR)  │      │ current_node     │
│ message_type (E) │      │ started_at       │
│ content (TEXT)   │      │ completed_at     │
│ metadata (JSON)  │      │ error_message    │
│ created_at       │      └──────────────────┘
└──────────────────┘
```

---

## File Count Breakdown

| Directory | Files | Lines of Code (est.) |
|-----------|-------|---------------------|
| apps/web/app/ | 8 pages | ~400 |
| apps/web/components/ | 10 components | ~600 |
| apps/web/lib/ | 1 utility | ~100 |
| apps/web/types/ | 1 type def | ~80 |
| apps/api/app/ | 5 files | ~300 |
| apps/api/agents/ | 7 files | ~500 |
| apps/api/core/ | 4 files | ~200 |
| apps/api/models/ | 1 file | ~100 |
| apps/api/migrations/ | 1 file | ~80 |
| Config/root | 8 files | ~100 |
| **Total** | **~46 files** | **~2,460 lines** |

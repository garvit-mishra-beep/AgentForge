# Conventions — AgentForge

---

## Monorepo Structure (Turborepo)

```
agentforge/
├── apps/                    # Deployable applications
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI backend
├── packages/                # Shared libraries
│   ├── db/                  # Prisma schema + client
│   ├── types/               # TypeScript types
│   └── ui/                  # React component library
├── docker-compose.yml       # Local infrastructure
├── turbo.json               # Pipeline configuration
└── package.json             # Workspace root
```

- Each `apps/*` directory is independently deployable
- Each `packages/*` directory is a buildable library consumed by `apps/*`
- No circular dependencies between packages

---

## File Naming

| Entity | Convention | Examples |
|--------|------------|----------|
| React components | `PascalCase.tsx` | `TeamGrid.tsx`, `AgentMessage.tsx`, `OutputPanel.tsx` |
| TypeScript utilities | `kebab-case.ts` | `api-client.ts`, `ws-client.ts`, `format-tokens.ts` |
| TypeScript types | `index.ts` in `packages/types/` | Named exports: `AgentRole`, `TaskStatus`, `WSEvent` |
| API routes (Next.js) | `route.ts` inside `app/api/v1/{resource}/` | `app/api/v1/tasks/route.ts` |
| API routes (FastAPI) | `snake_case.py` | `projects.py`, `teams.py`, `task_stream.py` |
| Pydantic models | `snake_case.py` in `models/` | `schemas.py` with classes `TaskCreate`, `TaskResponse` |
| Agent nodes | `snake_case_node.py` | `team_lead_node.py`, `backend_node.py` |
| Prompt templates | `snake_case.jinja2` | `team_lead.jinja2`, `reviewer.jinja2` |
| Database tables | `snake_case` (plural) | `task_steps`, `agent_memories`, `project_members` |
| Database columns | `snake_case` | `created_at`, `total_tokens`, `file_path` |
| Prisma models | `PascalCase` (singular) | `model TaskStep`, `model AgentMemory` |

---

## API Route Naming

```
GET    /api/v1/projects                  # List projects
POST   /api/v1/projects                  # Create project
GET    /api/v1/projects/{id}             # Get project
PATCH  /api/v1/projects/{id}             # Update project
DELETE /api/v1/projects/{id}             # Delete project

GET    /api/v1/projects/{id}/teams       # List teams in project
POST   /api/v1/projects/{id}/teams       # Create team in project

GET    /api/v1/teams/{id}/agents         # List agents on team
POST   /api/v1/teams/{id}/agents         # Add agent to team
DELETE /api/v1/teams/{id}/agents/{aid}   # Remove agent from team

POST   /api/v1/tasks                     # Create task
GET    /api/v1/tasks/{id}                # Get task with all steps
GET    /api/v1/tasks/{id}/steps          # Get task steps
GET    /api/v1/tasks/{id}/output         # Get generated files
POST   /api/v1/tasks/{id}/revise        # Request revision

GET    /api/v1/history                   # Task history (filters: project, status, date_from, date_to)
```

---

## TypeScript Conventions

```typescript
// Strict mode enabled. No `any`.

// Use explicit return types
export function formatTokens(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`;
  return count.toString();
}

// Interfaces for objects, types for unions
export type TaskStatus = "pending" | "running" | "completed" | "failed";

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  createdAt: string;
}

// Use branded types for IDs
export type TaskId = string & { readonly __brand: "TaskId" };
```

---

## Python / FastAPI Conventions

```python
# Type hints on all function signatures
# Use `X | None` instead of `Optional[X]`

from pydantic import BaseModel

class TaskCreate(BaseModel):
    project_id: str
    team_id: str
    title: str
    description: str

class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    total_tokens: int
    total_cost: float

# Async routes
@router.post("/tasks")
async def create_task(body: TaskCreate, user: User = Depends(get_current_user)) -> TaskResponse:
    ...
```

---

## Git Branch Naming

```
feat/jwt-auth                # New feature
fix/websocket-keepalive      # Bug fix
chore/update-deps            # Maintenance
docs/api-reference           # Documentation
refactor/agent-graph         # Refactoring
test/agent-node-coverage     # Testing
```

---

## Commit Message Format

```
type(scope): short description

[optional body]
```

### Types

- `feat` — New feature
- `fix` — Bug fix
- `chore` — Maintenance, tooling, dependencies
- `docs` — Documentation
- `refactor` — Code restructuring
- `test` — Adding or updating tests
- `perf` — Performance improvement

### Examples (from this codebase)

```
feat(api): add JWT verification endpoint with Clerk middleware

Implement POST /api/v1/auth/verify that validates Clerk JWTs,
extracts user_id, and returns user profile data.

fix(ws): add ping/pong keepalive to prevent silent disconnection after 5 min

WebSocket connections now send a ping frame every 30 seconds.
Connections that don't respond within 10 seconds are closed cleanly.

chore(deps): upgrade langgraph to 0.2.15

Fixes conditional edge routing bug in subgraph execution.

docs(schema): add agent_memories table definition and IVFFLAT index

docs(api): add WebSocket event reference for all event types

test(agents): add unit tests for team_lead node with mocked Gemini

Covers plan generation, error handling, and empty response cases.
```

---

## Database Conventions

- All tables have `id` (UUID, PK) and `created_at` (TIMESTAMPTZ)
- Foreign keys use the singular form: `project_id`, not `projects_id`
- Soft deletes use `is_active` boolean (not DELETE statements)
- Indexes named: `idx_{table}_{column}` or `idx_{table}_{col1}_{col2}` for composite
- Unique constraints named: `uq_{table}_{columns}`
- All CHECK constraints explicitly named

## Agent Node Conventions

```python
# Every agent node follows this signature:
async def node_name(state: AgentState) -> AgentState:
    """One-sentence description of what this node does."""

    # 1. Build system prompt from template
    prompt = render_prompt("role_name.jinja2", state=state)

    # 2. Call AI provider
    response = await ai_provider.chat(
        model=state.team_config[node.role],
        system=prompt,
        messages=[{"role": "user", "content": state.task.description}],
    )

    # 3. Validate output structure
    parsed = validate_agent_output(response, expected_schema)

    # 4. Update state
    state.agent_outputs[node.role] = parsed
    state.current_step = next_step
    state.total_tokens += parsed.tokens_used

    return state
```

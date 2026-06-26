# Technical Specification — AgentForge

**Version:** 1.0 | **Status:** Draft | **Last Updated:** June 2026

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Browser (Next.js 15)                          │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌────────┐ │
│  │Dashboard │  │Team      │  │Task View   │  │History   │  │Settings│ │
│  │          │  │Builder   │  │            │  │          │  │        │ │
│  └─────┬────┘  └─────┬────┘  └──────┬─────┘  └────┬─────┘  └───┬────┘ │
│        └──────────────┴──────────────┴──────────────┴────────────┘      │
│                              │                                          │
│                    ┌─────────┴─────────┐                                │
│                    │   API Client      │  (lib/api-client.ts)           │
│                    │  WebSocket Client │  (lib/ws-client.ts)            │
│                    └─────────┬─────────┘                                │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │ HTTP (REST) / WS (WebSocket)
                               │
┌──────────────────────────────┼──────────────────────────────────────────┐
│                    Vercel    │    (CDN + Serverless)                     │
│              ┌───────────────┴───────────────┐                          │
│              │   Next.js API Routes (BFF)    │  (apps/web/app/api/)     │
│              └───────────────┬───────────────┘                          │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────────┐
│                     Railway  │    (Docker Container)                    │
│  ┌───────────────────────────┴───────────────────────────┐              │
│  │                   FastAPI (Python)                     │             │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐  │             │
│  │  │REST      │  │WebSocket │  │Agent Orchestrator   │  │             │
│  │  │Handlers │  │Manager   │  │(LangGraph)          │  │             │
│  │  └────┬─────┘  └────┬─────┘  └──────────┬──────────┘  │             │
│  │       │             │                    │              │             │
│  │  ┌────┴─────────────┴────────────────────┴──────────┐  │             │
│  │  │              Core Services                        │  │             │
│  │  │  Auth (Clerk) │ DB (asyncpg) │ Redis (redis-py)  │  │             │
│  │  │  AI Providers │ Model Registry │ Memory Service   │  │             │
│  │  └──────────────────────────────────────────────────┘  │             │
│  └───────────────────────────────────────────────────────┘              │
│                           │              │                               │
│  ┌────────────────────────┘              └────────────────────────┐     │
│  │  Managed PostgreSQL + pgvector         │  Managed Redis          │     │
│  │  (Railway)                             │  (Railway)              │     │
│  │  • users, projects, teams, tasks       │  • Pub/sub channels     │     │
│  │  • agent_memories (vector index)       │  • JWT session cache    │     │
│  │  • task_steps, messages, outputs       │  • Rate limit counters   │     │
│  └───────────────────────────────────────┘  └────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┼───────────────────┐
               │               │                   │
        ┌──────┴──────┐ ┌──────┴──────┐    ┌───────┴───────┐
        │ OpenAI API  │ │Anthropic API│    │Google AI API  │
        │ (GPT-4o)    │ │(Claude)     │    │(Gemini)       │
        └─────────────┘ └─────────────┘    └───────────────┘
```

---

## Component Breakdown

### Frontend (apps/web)

| Component | Type | Purpose |
|-----------|------|---------|
| `app/dashboard/page.tsx` | Server | Project list, recent tasks, team status cards |
| `app/team-builder/page.tsx` | Client | Drag-and-drop role-to-model assignment grid |
| `app/tasks/[id]/page.tsx` | Client | Main workspace — live agent chat, output panel, file diff, approve/reject |
| `app/history/page.tsx` | Server | Searchable task history with filters (project, role, model, date) |
| `components/AgentMessage.tsx` | Client | Renders single agent output with role badge and model label |
| `components/OutputPanel.tsx` | Client | Displays generated files with syntax-highlighted diff viewer |
| `components/TeamGrid.tsx` | Client | Drag-and-drop grid for role↔model assignment |
| `lib/api-client.ts` | Shared | Typed fetch wrapper with Clerk JWT injection |
| `lib/ws-client.ts` | Shared | WebSocket client with auto-reconnect and event dispatch |

### Backend (apps/api)

| Module | Purpose |
|--------|---------|
| `app/routes/auth.py` | Clerk JWT verification endpoint |
| `app/routes/projects.py` | Project CRUD |
| `app/routes/teams.py` | Team and agent assignment CRUD |
| `app/routes/tasks.py` | Task creation, status polling, history |
| `app/ws/task_stream.py` | WebSocket handler — subscribes to Redis pub/sub and pushes to browser |
| `agents/graph.py` | LangGraph state graph definition (nodes, edges, conditional routing) |
| `agents/nodes/` | Individual agent step implementations (team_lead, backend, reviewer, qa, security, devops) |
| `agents/orchestrator.py` | High-level orchestrator — creates graph, invokes with state, handles errors |
| `core/auth.py` | FastAPI middleware — Clerk JWT validation, user_id extraction |
| `core/database.py` | asyncpg connection pool setup |
| `core/redis.py` | Redis client and pub/sub manager |
| `core/model_registry.py` | Supported models, context windows, rate limits |
| `models/schemas.py` | Pydantic request/response models |

### Agent Layer

| Component | Description |
|-----------|-------------|
| `LangGraph State` | TypedDict with fields: task, plan, current_step, agent_outputs, errors, status |
| `Supervisor Node` | Routes execution to the correct agent node based on workflow phase |
| `Agent Nodes` | Each node: builds system prompt → calls AI provider → validates output → returns state update |
| `Handoff Protocol` | Each node writes to state.current_step and state.agent_outputs; next node reads its input |
| `Human-in-the-Loop` | LangGraph interrupts at handoff gates; human approves or requests revision via REST call |

---

## Data Flow — Full Task Execution

### Example: "Build JWT Authentication"

```
Step 0: User creates task via POST /api/v1/tasks
        Body: { project_id, team_id, description: "Build JWT Authentication" }
        → Task inserted into DB with status "pending"
        → WebSocket event: task_created

Step 1: Orchestrator picks up task
        → Loads team config (roles and model assignments)
        → Initializes LangGraph state
        → WebSocket event: task_started

Step 2: Team Lead Node (Gemini 1.5 Pro)
        Input: task description + codebase summary
        Action: analyzes requirements, creates subtask plan
        Output: structured plan with subtask list, acceptance criteria, file list
        → State updated: state.plan
        → Redis pub/sub → WebSocket: agent_started → agent_message → agent_complete

Step 3: Supervisor reads state.plan, routes to Backend Engineer
        → State updated: state.current_step = "backend_implementation"

Step 4: Backend Engineer Node (Claude Sonnet)
        Input: subtask list + codebase context + file contents
        Action: implements JWT service, auth endpoints, DB migration
        Output: code files with file paths and contents
        → State updated: state.agent_outputs["backend"] = { files, summary }
        → Redis pub/sub → WebSocket: agent_started → agent_message → agent_complete

Step 5: Supervisor routes to Reviewer
        → State updated: state.current_step = "review"

Step 6: Reviewer Node (GPT-4o)
        Input: backend output + acceptance criteria
        Action: reviews code for correctness, edge cases, performance
        Output: structured review with blocking/non-blocking issues per file+line
        → State updated: state.agent_outputs["reviewer"] = { issues, verdict }
        → Supervisor checks: if blocking issues exist → route back to Backend (Step 4)

Step 7: (Conditional) Backend Engineer applies review feedback → re-outputs

Step 8: Supervisor routes to QA Engineer

Step 9: QA Engineer Node (Qwen-72B)
        Input: final implementation
        Action: generates unit tests, integration tests, runs validation
        Output: test files + test results report
        → State updated: state.agent_outputs["qa"] = { tests, results }
        → If tests fail → route back to Backend (Step 4)

Step 10: Supervisor routes to Security Engineer

Step 11: Security Engineer Node (GPT-4o)
         Input: implementation + test report
         Action: audits JWT signing, expiry, refresh rotation, session invalidation
         Output: security findings report (critical/high/medium/low)
         → State updated: state.agent_outputs["security"]
         → If critical findings → block delivery, escalate to human

Step 12: Supervisor routes to Team Lead (final review)

Step 13: Team Lead Node (Gemini 1.5 Pro)
         Input: all agent outputs
         Action: reviews against original acceptance criteria, writes summary
         Output: delivery package (code + tests + review + security report + summary)
         → State updated: state.final_output
         → WebSocket: task_complete

Step 14: Human receives delivery package
         Action: approve or request changes
         → If changes requested → POST /api/v1/tasks/{id}/revise → restart from Step 2
         → If approved → task status set to "completed"
```

---

## WebSocket Event Schema

```typescript
// All WebSocket events follow this structure:

interface WSEvent {
  type: WSEventType;
  task_id: string;
  agent_id?: string;
  role?: string;
  model?: string;
  timestamp: string; // ISO 8601
  payload: Record<string, unknown>;
}

enum WSEventType {
  TASK_CREATED     = "task_created",
  TASK_STARTED     = "task_started",
  TASK_COMPLETE    = "task_complete",
  TASK_ERROR       = "task_error",
  AGENT_STARTED    = "agent_started",
  AGENT_MESSAGE    = "agent_message",   // Streamed token chunks
  AGENT_COMPLETE   = "agent_complete",
  HANDOFF          = "handoff",          // Agent A → Agent B
  HUMAN_INTERRUPT  = "human_interrupt",  // Waiting for human approval
  HUMAN_APPROVED   = "human_approved",
  HUMAN_REJECTED   = "human_rejected",
}
```

---

## LangGraph Agent Graph

```python
# Conceptual structure of agents/graph.py

from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)

# Nodes
graph.add_node("team_lead_plan", team_lead_plan_node)
graph.add_node("backend_implement", backend_implement_node)
graph.add_node("review", review_node)
graph.add_node("qa", qa_node)
graph.add_node("security", security_node)
graph.add_node("team_lead_deliver", team_lead_deliver_node)

# Edges
graph.add_edge("team_lead_plan", "backend_implement")

# Conditional: route back if review has blocking issues
graph.add_conditional_edges(
    "review",
    review_router,  # Returns "backend_implement" or "qa"
    {"backend_implement": "backend_implement", "qa": "qa"}
)

# Conditional: route back if tests fail
graph.add_conditional_edges(
    "qa",
    qa_router,  # Returns "backend_implement" or "security"
    {"backend_implement": "backend_implement", "security": "security"}
)

graph.add_conditional_edges(
    "security",
    security_router,  # Returns "team_lead_deliver" or END (if critical blocks)
    {"team_lead_deliver": "team_lead_deliver", END: END}
)

graph.add_edge("team_lead_deliver", END)

graph.set_entry_point("team_lead_plan")
```

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| LangGraph over raw agent loop | Explicit DAG, state persistence, conditional routing, human-in-the-loop interrupts |
| FastAPI over Express | Python ecosystem for LangGraph + AI SDKs; async WebSocket support |
| Clerk over Auth.js | Hosted UI, organization management for Team plan; webhook lifecycle events |
| PostgreSQL over MongoDB | Relational data (projects→teams→agents→tasks→steps); pgvector for semantic search |
| Redis pub/sub over polling | Sub-millisecond event propagation; native pub/sub channels per task |
| WebSockets over SSE | Bidirectional communication needed for human approval signals |
| Turborepo over Nx | Simpler configuration; native pnpm workspace support; faster for this scale |
| Railway over AWS | Managed Postgres + Redis; simpler deployment; sufficient for current scale |

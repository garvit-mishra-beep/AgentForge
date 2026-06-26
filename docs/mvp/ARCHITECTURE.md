# Architecture — AgentForge MVP

**Version:** MVP v0.1 | **Status:** Blueprint | **Last Updated:** June 2026

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js 15)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │Dashboard │  │Team      │  │Task Execution View           │  │
│  │/teams    │  │/teams/[id]│  │/tasks/[id]                   │  │
│  └─────┬────┘  └─────┬────┘  └──────────────┬───────────────┘  │
│        └──────────────┴──────────────────────┘                  │
│                         │                                       │
│                  ┌──────┴──────┐                                │
│                  │  lib/api.ts  │  (fetch wrapper)               │
│                  └──────┬──────┘                                │
└─────────────────────────┼────────────────────────────────────────┘
                          │ HTTP REST (JSON)
                          │
┌─────────────────────────┼────────────────────────────────────────┐
│                 FastAPI (Python 3.11+)                            │
│  ┌──────────────────────┴──────────────────────┐                 │
│  │              FastAPI Application              │               │
│  │  ┌────────────┐  ┌────────────┐             │                 │
│  │  │ /api/teams │  │ /api/tasks │  /ws/task   │                 │
│  │  └─────┬──────┘  └──────┬─────┘             │                 │
│  │        └────────────────┘                    │                 │
│  └──────────────────────┬──────────────────────┘                 │
│                         │                                        │
│  ┌──────────────────────┴──────────────────────┐                 │
│  │           Agent Orchestrator                  │               │
│  │  ┌─────────────────────────────────────────┐ │                 │
│  │  │         LangGraph StateGraph             │ │               │
│  │  │                                          │ │               │
│  │  │  START → TeamLead → Builder → Reviewer   │ │               │
│  │  │              → TeamLeadFinal → END       │ │               │
│  │  └─────────────────────────────────────────┘ │               │
│  │                                              │               │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ │               │
│  │  │  OpenAI    │ │  Anthropic │ │  Google  │ │               │
│  │  │  Provider  │ │  Provider  │ │  Provider│ │               │
│  │  └────────────┘ └────────────┘ └──────────┘ │               │
│  └──────────────────────┬──────────────────────┘                 │
│                         │                                        │
│  ┌──────────────────────┴──────────────────────┐                 │
│  │             Core Services                     │               │
│  │  ┌──────────┐  ┌──────────┐                 │               │
│  │  │ asyncpg  │  │ Config   │                 │               │
│  │  │ Pool     │  │ .env     │                 │               │
│  │  └────┬─────┘  └──────────┘                 │               │
│  └───────┼────────────────────────────────────┘                 │
└──────────┼────────────────────────────────────────────────────────┘
           │
┌──────────┴──────────┐
│    PostgreSQL 16     │
│  ┌────────────────┐  │
│  │ users          │  │
│  │ teams          │  │
│  │ team_members   │  │
│  │ tasks          │  │
│  │ task_messages  │  │
│  │ executions     │  │
│  └────────────────┘  │
└─────────────────────┘
```

---

## Core Design Decisions

### 1. Single Database, No Redis (MVP)

PostgreSQL is the single source of truth. No Redis in MVP. Task status polling uses HTTP GET with short intervals (1s). This eliminates an infrastructure dependency while the hypothesis is being validated.

**Trade-off:** Polling adds ~500ms latency vs WebSocket push. Acceptable for MVP.

**When to add Redis:** After reaching 100 concurrent active tasks.

### 2. Sequential Agent Execution (No Parallelism)

Agents run one at a time in a chain: Team Lead → Builder → Reviewer → Team Lead Final. No parallel execution for MVP. This simplifies the state machine, eliminates race conditions, and makes debugging straightforward.

**Trade-off:** Task completion takes 3-5 minutes instead of 1-2 minutes with parallelism.

**When to add parallelism:** After proving multi-agent hypothesis with 100+ real users.

### 3. Direct AI Provider SDK Calls (No LangChain)

Each agent node calls the AI provider SDK directly (openai, anthropic, google-generativeai). No LangChain abstraction layer. This reduces dependencies, makes debugging easier, and avoids vendor lock-in at the SDK level.

**Trade-off:** More code per provider. Each node has explicit provider call logic.

**When to add abstraction:** When supporting 5+ providers with complex fallback chains.

### 4. Stateless API, Stateful Graph

API servers are stateless. All task state lives in PostgreSQL. LangGraph state is serialized to the `executions.graph_state` JSONB column on each step transition. This means the API can be horizontally scaled without sticky sessions.

### 5. System Prompts as Jinja2 Templates

All agent system prompts live in `apps/api/agents/prompts/*.jinja2`. They are rendered at execution time with task-specific variables. No prompt text is hardcoded in Python code.

---

## Data Flow — Task Execution

```
Step 0: User creates task via POST /api/v1/tasks
         Body: { team_id, title, description }
         → Task inserted with status "pending"
         → Returns task_id immediately

Step 1: User polls GET /api/v1/tasks/{id} (every 1s)
         → Status transitions: pending → running

Step 2: Orchestrator executes LangGraph:
         ┌─────────────────────────────────────────────┐
         │  Graph Execution                             │
         │                                              │
         │  Node 1: Team Lead (plan)                    │
         │    Input: task description, team config      │
         │    Output: structured plan with subtasks     │
         │    → INSERT task_message (role=team_lead)    │
         │                                              │
         │  Node 2: Builder (implement)                 │
         │    Input: plan, task description              │
         │    Output: code, summary                     │
         │    → INSERT task_message (role=builder)      │
         │                                              │
         │  Node 3: Reviewer (review)                   │
         │    Input: builder output, plan               │
         │    Output: review findings, verdict          │
         │    → INSERT task_message (role=reviewer)     │
         │                                              │
         │  Node 4: Team Lead (deliver)                 │
         │    Input: all prior outputs                  │
         │    Output: final delivery summary            │
         │    → INSERT task_message (role=team_lead)    │
         │    → UPDATE task status = "completed"        │
         └─────────────────────────────────────────────┘

Step 3: User polls sees status = "completed"
         GET /api/v1/tasks/{id}/messages
         → Returns all task_messages in order

Step 4: UI displays execution timeline:
         Step 1: Team Lead Planning    [Complete]
         Step 2: Builder Working       [Complete]
         Step 3: Reviewer Reviewing    [Complete]
         Step 4: Final Delivery        [Complete]
```

---

## LangGraph State Definition

```python
from typing import TypedDict, List, Optional

class AgentOutput(TypedDict):
    role: str
    model: str
    content: str
    message_type: str  # plan | code | review | delivery | error
    metadata: dict

class TaskInfo(TypedDict):
    id: str
    title: str
    description: str

class TeamMember(TypedDict):
    role: str
    model: str
    provider: str  # openai | anthropic | google

class AgentState(TypedDict):
    task: TaskInfo
    team: List[TeamMember]
    plan: Optional[str]           # Team Lead output
    builder_output: Optional[str]  # Builder output
    review: Optional[str]         # Reviewer output
    delivery: Optional[str]       # Final delivery
    current_step: str             # Which agent is active
    messages: List[AgentOutput]   # All prior messages
    errors: List[str]             # Any errors encountered
```

---

## API Endpoints (MVP)

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/v1/teams | Create a team |
| GET | /api/v1/teams | List teams |
| GET | /api/v1/teams/{id} | Get team with members |
| PUT | /api/v1/teams/{id} | Update team |
| DELETE | /api/v1/teams/{id} | Delete team |
| POST | /api/v1/teams/{id}/members | Add team member (agent) |
| DELETE | /api/v1/teams/{id}/members/{mid} | Remove team member |
| POST | /api/v1/tasks | Create a task (triggers execution) |
| GET | /api/v1/tasks | List tasks |
| GET | /api/v1/tasks/{id} | Get task with status |
| GET | /api/v1/tasks/{id}/messages | Get all messages for a task |

---

## Provider Integration

Each AI provider is wrapped in a thin adapter:

```python
# core/providers.py

class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
    ) -> str: ...

class OpenAIProvider(AIProvider):
    async def chat(self, model, system_prompt, user_message):
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,  # Low temperature for code generation
        )
        return response.choices[0].message.content or ""

class AnthropicProvider(AIProvider):
    async def chat(self, model, system_prompt, user_message):
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=8192,
            temperature=0.2,
        )
        return response.content[0].text

class GoogleProvider(AIProvider):
    async def chat(self, model, system_prompt, user_message):
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = await client.aio.models.generate_content(
            model=model,
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            ),
        )
        return response.text
```

---

## Error Handling Strategy

| Error Type | Handling | User Impact |
|-----------|----------|-------------|
| AI provider timeout | Retry 2x with 2s backoff | Delayed by ~10s |
| AI provider 429/rate limit | Wait 5s, retry 1x | Delayed by ~10s |
| AI provider 5xx | Fail gracefully, set task status=failed | Task fails, show error in UI |
| Invalid model name | Validate before execution | Prevented at team creation |
| Database connection loss | Retry with backoff (3x) | Temporary unavailability |
| Malformed agent output | Parse validation, retry with error context | Slightly delayed |

---

## Security (MVP)

- No authentication in MVP (single-user mode)
- AI provider API keys read from environment variables only
- API keys never stored in database
- CORS restricted to frontend origin
- Rate limiting via middleware (100 req/min per IP)

---

## Performance Targets (MVP)

| Metric | Target |
|--------|--------|
| Team creation | < 200ms |
| Task creation | < 500ms (async execution) |
| Task status poll | < 100ms |
| Message retrieval | < 200ms |
| Average task completion | < 5 minutes |
| Concurrent tasks | 10 |

---

## Out of Scope (MVP)

| Feature | Reason |
|---------|--------|
| Authentication | MVP is single-user. Adding auth = 40% more code, 0% more hypothesis validation |
| WebSocket streaming | Polling is simpler, works for MVP scale. Add WS when latency becomes a complaint |
| Redis | Not needed until 100+ concurrent tasks or WebSocket is added |
| Agent memory (pgvector) | Not needed to prove multi-agent hypothesis |
| Billing | No paid tier yet |
| Multi-project | Single workspace |
| File outputs | Messages contain structured text only |
| Frontend Engineer role | Only 3 roles: Lead, Builder, Reviewer |
| QA Engineer role | Reviewer covers validation in MVP |
| Security Engineer role | Out of scope |
| DevOps Engineer role | Out of scope |

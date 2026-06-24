# AgentForge AI — Architecture

## High Level Architecture

```mermaid
graph TB
    subgraph Clients
        WEB["Web App (Next.js 15)"]
        API["External API Clients"]
        WIDGET["Embedded Chat Widget"]
        BOTS["Slack / Discord Bot"]
    end

    subgraph Gateway
        ALB["Load Balancer"]
        CDN["CDN / Edge"]
    end

    subgraph "API Layer (FastAPI)"
        GW["REST API Gateway"]
        WS["WebSocket Server"]
        AUTH["Clerk Auth"]
        RATELIMIT["Rate Limiter"]
    end

    subgraph "Core Engine"
        AM["Agent Manager"]
        WM["Workflow Manager (LangGraph)"]
        TM["Tool Executor"]
        MEM["Memory Manager"]
        RAG["RAG Engine"]
    end

    subgraph "Data Layer"
        PG[("PostgreSQL<br/>Agents, Workflows,<br/>Users, Executions")]
        VDB[("Qdrant<br/>Vector Store<br/>Memory + RAG")]
        REDIS[("Redis<br/>Cache + Queue<br/>+ Sessions")]
        FS[("Object Storage<br/>Documents + Artifacts")]
    end

    subgraph "Observability"
        OTL["OpenTelemetry Collector"]
        PROM["Prometheus"]
        GRAF["Grafana"]
    end

    subgraph "AI Providers"
        OPENAI["OpenAI"]
        ANTHRO["Anthropic"]
        GEMINI["Gemini"]
        OLLAMA["Ollama (Local)"]
    end

    WEB --> CDN --> ALB --> GW
    API --> ALB --> GW
    WIDGET --> CDN --> ALB --> WS
    BOTS --> ALB --> GW

    GW --> AUTH
    GW --> RATELIMIT
    GW --> AM
    GW --> WS

    AM --> TM
    AM --> MEM
    AM --> RAG
    AM --> WM

    WM --> OPENAI
    WM --> ANTHRO
    WM --> GEMINI
    WM --> OLLAMA

    AM --> PG
    AM --> REDIS
    TM --> REDIS
    MEM --> VDB
    MEM --> REDIS
    RAG --> VDB
    RAG --> FS

    AM --> OTL
    WM --> OTL
    OTL --> PROM
    PROM --> GRAF
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as API Gateway
    participant AUTH as Clerk Auth
    participant AM as Agent Manager
    participant WM as Workflow Engine
    participant LLM as LLM Provider
    participant MEM as Memory
    participant TOOL as Tool Executor
    participant DB as PostgreSQL
    participant OTL as OpenTelemetry

    C->>GW: POST /api/v1/agents/:id/invoke
    GW->>AUTH: Validate API Key
    AUTH-->>GW: User Identity
    GW->>AM: route to agent

    AM->>DB: load agent config
    DB-->>AM: agent definition

    AM->>MEM: load context (memory)
    MEM-->>AM: conversation history

    AM->>WM: execute with state

    WM->>LLM: prompt + tools
    LLM-->>WM: response + tool calls

    alt Tool Calls
        WM->>TOOL: execute tool
        TOOL-->>WM: tool result
        WM->>LLM: continue with result
        LLM-->>WM: final response
    end

    WM->>MEM: store conversation
    WM-->>AM: final output

    AM->>DB: persist execution log
    AM->>OTL: emit trace

    AM-->>GW: response
    GW-->>C: 200 JSON + stream
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant FE as Next.js Frontend
    participant CLERK as Clerk
    participant API as FastAPI Backend
    participant DB as PostgreSQL

    C->>FE: Login request
    FE->>CLERK: OAuth / Email / SSO
    CLERK-->>FE: Session Token (JWT)
    FE->>API: Request + Bearer token
    API->>CLERK: Verify JWT
    CLERK-->>API: User identity
    API->>DB: Authorize (RBAC)
    DB-->>API: Permissions
    API-->>FE: Response

    Note over FE,API: API key alternative for machine-to-machine
    C->>API: POST /api/v1/agent/invoke + X-API-Key
    API->>DB: Validate API Key
    DB-->>API: Tenant + Agent ID
    API-->>C: Response
```

## Agent Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft: Create Agent
    Draft --> Active: Configure + Save
    Active --> Invoking: API Call
    Invoking --> Processing: LLM Round
    Processing --> ToolCall: Tool Required
    ToolCall --> Processing: Tool Result
    Processing --> Complete: Final Response
    Complete --> Active: Idle
    Active --> Archived: Deactivate
    Active --> Draft: Edit
    Archived --> [*]: Delete
```

## Workflow Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft: Create
    Draft --> Published: Compile + Validate
    Published --> Executing: Trigger
    Executing --> StepN: Agent 1..N
    StepN --> Branching: Conditional
    Branching --> Executing: Next Step
    Executing --> Completed: All Steps Done
    Executing --> Failed: Error (with retries)
    Executing --> Cancelled: User Cancel
    Completed --> [*]
    Failed --> Executing: Retry
    Failed --> [*]: Exhausted
    Published --> Draft: Edit
```

## Directory Structure (Conceptual)

```
agentforge/
├── apps/
│   ├── web/                  # Next.js 15 frontend
│   └── api/                  # FastAPI backend
├── packages/
│   ├── agents/               # Agent runtime & abstractions
│   ├── workflows/            # LangGraph workflow definitions
│   ├── tools/                # Tool implementations
│   ├── memory/               # Memory backends
│   ├── rag/                  # RAG pipeline
│   ├── llm/                  # LLM provider abstractions
│   ├── observability/        # OpenTelemetry setup
│   └── shared/               # Shared types & utilities
├── infrastructure/
│   ├── docker/               # Dockerfiles
│   ├── terraform/            # Infrastructure as Code
│   └── kubernetes/           # K8s manifests
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── adr/
│   ├── guides/
│   └── api/
├── scripts/
│   ├── setup.sh
│   └── seed.sh
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE/
├── docker-compose.yml
├── Makefile
└── README.md
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Monorepo | Turborepo | Shared types, unified CI, easier refactoring |
| API Framework | FastAPI | Async-native, auto-docs, Python ecosystem |
| Database | PostgreSQL | Reliability, JSON support, pgvector for embeddings |
| Vector Store | Qdrant | High-performance, self-hostable, gRPC API |
| Workflow Engine | LangGraph | State graphs, checkpointing, built for agents |
| Auth | Clerk | Managed auth, multi-provider, webhook support |
| Frontend | Next.js 15 | App Router, React 19, SSR, Server Actions |
| Observability | OpenTelemetry | Vendor-neutral, wide adoption, rich exporters |

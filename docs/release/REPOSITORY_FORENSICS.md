# Repository Forensics

`Version: 1.0` · `Scope: Full-Stack Source & Dependency Telemetry`

This document outlines the structural truth of the AgentForge repository, generated via recursive code inventory scanning. All metrics are validated against current file pathways, imports, and decorators.

---

## 1. Code Statistics

| Category | Count | Scope / Details |
| :--- | :--- | :--- |
| **Total Files** | **774** | Excluding virtual environments (`venv`, `.venv`), `node_modules`, `.git`, `.next`, and build caches. |
| **Total Source Files** | **526** | Total files containing logic: **449** Python, **76** TypeScript/React, **1** CSS. |
| **Total Source Lines** | **~64,000** | Across Python application modules and frontend pages/components. |
| **Total Test Files** | **35** | Python unit/E2E test suites inside `apps/api/tests/` and `apps/cli/tests/`. |
| **Total API Endpoints** | **82** | Documented FastAPI route paths (`@router.<method>`) across 14 router modules. |
| **Total UI Pages** | **20** | Next.js App Router route entry pages (`page.tsx`) or API handlers (`route.ts`). |
| **Total DB Migrations** | **22** | Incremental SQL migration scripts inside `apps/api/migrations/`. |
| **Total DB Tables** | **30** | Implemented relational tables tracked across database migrations. |
| **Total UI Components** | **36** | React components under `apps/web/components/`. |
| **Total React Hooks** | **2** | Context-driven hooks (`useToast`, `useAuth`) declared within the frontend. |
| **Total Core Services** | **4** | Sandbox executor, Test executor, Feedback manager, Memory service. |
| **Total CLI Commands** | **12** | Click commands inside `apps/cli/agentforge_cli/`. |

---

## 2. Architectural Dependency Graph

The following Mermaid diagrams represent the exact import bindings and runtime dependencies of the system:

### 2.1 Request & Auth Pipeline
```mermaid
graph TD
    UI[Next.js Client] -->|HTTPS REST| API[FastAPI Entrypoint: main.py]
    UI -->|WebSocket| WS[Websocket Router: app/routes/tasks.py]
    
    subgraph FastAPI Middleware Stack
        API --> CORS[CORSMiddleware]
        CORS --> RL[RateLimitMiddleware: core/redis.py]
        RL --> CID[CorrelationMiddleware: core/observability.py]
        CID --> Auth[AuthMiddleware: app/auth.py]
    end
    
    Auth --> Router[APIRouter Manager]
    
    subgraph Routers
        Router --> AuthR[routes/auth.py]
        Router --> TeamR[routes/teams.py]
        Router --> TaskR[routes/tasks.py]
        Router --> ProjR[routes/projects.py]
    end
```

### 2.2 Orchestrator & Task Execution Flow
```mermaid
graph TD
    TaskR[routes/tasks.py] -->|Trigger Task| Graph[Orchestrator LangGraph: apps/agents/graph.py]
    Graph -->|Node: plan| Lead[Team Lead Node]
    Graph -->|Node: build| Build[Builder Node]
    Graph -->|Node: review| Rev[Reviewer Node]
    
    Build -->|Create Code| Sandbox[Sandbox Executor: app/services/sandbox_executor.py]
    Sandbox -->|Execute Docker| Container[Python Docker Sandbox]
    
    Rev -->|Run Code Checks| TestExec[Test Executor: app/services/test_executor.py]
    TestExec -->|Verify Syntax / Run Pytest| Container
    
    Graph -->|Save Results| DB[(PostgreSQL Pool: core/database.py)]
    Graph -->|Save Context/Memory| PGV[(pgvector: app/memory_service.py)]
```

### 2.3 Frontend Dependency Architecture
```mermaid
graph TD
    Layout[App Layout: app/layout.tsx] --> AuthProvider[AuthContext: auth-context.tsx]
    AuthProvider --> ToastProvider[ToastContext: toast.tsx]
    ToastProvider --> SidebarProvider[Sidebar Layout Shell: app/layout.tsx]
    
    subgraph Pages
        SidebarProvider --> Dash[Dashboard: dashboard/page.tsx]
        SidebarProvider --> Teams[Teams Manager: teams/page.tsx]
        SidebarProvider --> Workspace[Task Workspace: tasks/page.tsx]
        SidebarProvider --> Settings[Settings Page: settings/page.tsx]
    end
    
    Dash & Teams & Workspace -->|REST API Client| Client[API Wrapper: lib/api.ts]
    Workspace -->|WS Event Broker| WSClient[Websocket Client: lib/ws-client.ts]
```

---

## 3. Directory Topology Mapping

```
AgentForge/
├── apps/
│   ├── agents/                   # LangGraph orchestration state definitions
│   │   └── graph.py
│   ├── api/                      # FastAPI core backend service
│   │   ├── app/                  # Main route handlers, controllers, integrations
│   │   │   ├── routes/           # REST endpoints and WebSocket handlers
│   │   │   ├── integrations/     # GitHub API services
│   │   │   └── services/         # Docker execute/test sandboxes
│   │   ├── core/                 # DB connectors, configs, rate-limiting, models
│   │   ├── migrations/           # SQL migration scripts (001-022)
│   │   └── models/               # Pydantic payloads and models
│   ├── cli/                      # Click-based developers command line
│   └── web/                      # Next.js App Router client application
├── app/                          # Repository Intelligence static analysis engines
│   ├── evidence_gate/            # Validation testing pipelines
│   ├── repository_intelligence/  # Code parser, chunker, indexer, call graphs
│   └── validation/               # Automatic criteria/acceptance spec testing
└── docs/                         # System architecture and release audits
```

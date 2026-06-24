# Architecture

## High-Level Architecture

```mermaid
graph TB
    subgraph "Clients"
        WB[Web Browser]
        API[API Clients]
        WS[WebSocket Clients]
    end

    subgraph "API Gateway Layer"
        NX[Next.js Frontend<br/>Port 3000]
        UV[Uvicorn ASGI Server<br/>Port 8000]
        MW[Middleware Stack<br/>Logging → RateLimit → Audit]
    end

    subgraph "Application Layer"
        RT[FastAPI Routes]
        SV[Services Layer]
        MD[SQLAlchemy Models]
        
        subgraph "Routes"
            AUTH[Auth Routes]
            AGT[Agent Routes]
            WKF[Workflow Routes]
            EXC[Execution Routes]
            RAG[RAG Routes]
            OBS[Observability Routes]
            WSOCK[WebSocket Routes]
        end
        
        subgraph "Services"
            AS[AgentService]
            WS[WorkflowService]
            ES[ExecutionService]
            ADS[AuditService]
            RS[RAGPipeline]
            VS[VectorStoreService]
        end
    end

    subgraph "Infrastructure"
        PG[(PostgreSQL<br/>Port 5432)]
        RD[(Redis<br/>Port 6379)]
        QD[(Qdrant<br/>Port 6333)]
    end

    subgraph "LLM Providers"
        OA[OpenAI]
        AN[Anthropic]
        GG[Google Gemini]
    end

    subgraph "Observability"
        PM[Prometheus Metrics<br/>Port 8000/metrics]
        OT[OpenTelemetry<br/>Port 4317]
        SL[Structured Logging<br/>JSON/Console]
    end

    WB --> NX
    NX --> UV
    API --> UV
    WS --> UV
    
    UV --> MW
    MW --> RT
    
    AUTH --> AS
    AGT --> AS
    WKF --> WS
    EXC --> ES
    RAG --> RS
    OBS --> ES
    
    AS --> MD
    WS --> MD
    ES --> MD
    ADS --> MD
    
    MD --> PG
    AS --> RD
    WS --> RD
    ES --> RD
    
    RS --> VS
    VS --> QD
    RS --> LLM_Models
    
    AS --> LLM_Models
    WS --> WFE[WorkflowEngine]
    WFE --> LLM_Models
    
    LLM_Models --> OA
    LLM_Models --> AN
    LLM_Models --> GG
    
    RT --> PM
    RT --> OT
    RT --> SL
```

## Module Map

```
agentforge/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── core/         # Config, database, security, health, metrics
│   │   ├── routes/       # API route handlers
│   │   ├── services/     # Business logic
│   │   ├── middleware/    # Logging, rate limiting, audit
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── dependencies/ # FastAPI dependency injection
│   └── web/              # Next.js frontend
│       ├── app/          # Next.js App Router pages
│       ├── components/   # React components
│       └── stores/       # Zustand state management
├── packages/
│   ├── agents/           # Agent orchestration
│   ├── llm/              # LLM provider abstraction
│   ├── memory/           # Memory/persistence
│   ├── observability/    # Shared observability primitives
│   ├── rag/              # RAG primitives
│   ├── shared/           # Shared types and utilities
│   ├── tools/            # Tool definitions
│   └── workflows/        # Workflow execution engine
├── infrastructure/       # Docker, Kubernetes, Terraform
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **API Framework** | FastAPI | Async Python web framework |
| **ORM** | SQLAlchemy 2.0 (async) | Database abstraction and migrations |
| **Database** | PostgreSQL 15 | Primary data store |
| **Cache** | Redis 7 | Session cache, WS pub/sub |
| **Vector DB** | Qdrant | Vector similarity search |
| **LLM** | LangChain + direct APIs | Multi-provider LLM orchestration |
| **Workflows** | LangGraph | Stateful agent workflow engine |
| **Frontend** | Next.js 15 + React | Web UI |
| **Auth** | JWT + API Keys | Authentication and authorization |
| **Monitoring** | Prometheus | Metrics collection |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **Logging** | structlog | Structured logging |
| **Async** | asyncio | Async runtime |
| **Build** | Turborepo | Monorepo build orchestration |

## Key Design Decisions

1. **Async-First**: API built on asyncio for high concurrency
2. **Multi-Tenant**: Tenant isolation at database query level
3. **Pluggable LLMs**: Provider abstraction via `LLMProvider` base class
4. **Lazy Vector Store**: Qdrant client initialized on first use only
5. **Defensive Security**: JWT validation, rate limiting, audit logging, safe expression evaluation

# Architecture Diagrams

## System Architecture

```mermaid
graph TB
    subgraph "Clients"
        WB[Web Browser]
        API[API Clients]
        WS[WebSocket Clients]
    end

    subgraph "API Layer"
        NX[Next.js Frontend<br/>Port 3000]
        UV[FastAPI ASGI Server<br/>Port 8000]
    end

    subgraph "Middleware"
        L[Logging Middleware]
        R[Rate Limit Middleware]
        A[Audit Middleware]
        M[Metrics Middleware]
    end

    subgraph "Routes"
        AGT[Agent Routes]
        WKF[Workflow Routes]
        EXC[Execution Routes]
        RAG[RAG Routes]
        AUTH[Auth Routes]
        OBS[Observability Routes]
    end

    subgraph "Services"
        AS[AgentService]
        WS[WorkflowService]
        ES[ExecutionService]
        AD[AuditService]
        RP[RAGPipeline]
        VS[VectorStoreService]
        LLM[LLM Provider]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        RD[(Redis)]
        QD[(Qdrant)]
    end

    subgraph "Observability"
        PM[/metrics]
        HC[/health /ready /live]
        LOG[Structured Logging]
    end

    WB --> NX --> UV
    API --> UV
    WS --> UV
    UV --> L --> R --> A
    A --> M --> AGT & WKF & EXC & RAG & AUTH & OBS
    AGT & WKF & EXC & RAG & AUTH --> AS & WS & ES & AD & RP
    AS & WS & ES & AD --> DB
    AS & WS & ES --> RD
    RP --> VS --> QD
    AS & WKF & RP --> LLM
    AGT & WKF & EXC & RAG & AUTH --> PM & HC & LOG
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx/LB
    participant F as FastAPI
    participant M as Middleware
    participant R as Route
    participant S as Service
    participant DB as Database
    participant LLM as LLM

    C->>N: HTTPS Request
    N->>F: Forward
    F->>M: Request
    M->>M: Rate Limit Check
    M->>M: Audit Log
    M->>R: Route Handler
    R->>R: Validate (Pydantic)
    R->>S: Business Logic
    S->>DB: Query (SQLAlchemy)
    DB-->>S: Result
    alt LLM Call Needed
        S->>LLM: Provider Call
        Note over S,LLM: Circuit Breaker + Retry
        LLM-->>S: Response
    end
    S-->>R: Data
    R-->>M: Response
    M-->>F: Response
    F->>F: Metrics
    F-->>N: Response
    N-->>C: HTTPS Response
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant AU as Auth Route
    participant DB as Database
    participant JWT as JWT Service

    Note over C,JWT: Login
    C->>F: POST /auth/token
    F->>AU: credentials
    AU->>DB: find user
    DB-->>AU: user + hash
    AU->>AU: verify_password()
    AU->>JWT: create tokens
    JWT-->>AU: access + refresh
    AU-->>C: tokens

    Note over C,JWT: Authenticated Request
    C->>F: GET /agents (Authorization: Bearer token)
    F->>F: Verify JWT
    F->>F: Extract tenant_id
    F->>C: Response (scoped to tenant)

    Note over C,JWT: Token Refresh
    C->>F: POST /auth/refresh
    F->>JWT: verify refresh token
    JWT-->>F: new access token
    F-->>C: new access token
```

## Workflow Execution

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Workflow Routes
    participant WE as WorkflowEngine
    participant LLM as LLM Provider
    participant T as Tools
    participant DB as Database

    C->>R: POST /agents/{id}/invoke
    R->>WE: execute workflow
    Note over WE: Load workflow definition

    loop Each Node
        WE->>WE: evaluate node type
        
        alt LLM Node
            WE->>LLM: generate
            LLM-->>WE: response
        else Tool Node
            WE->>T: execute tool
            T-->>WE: result
        else Condition Node
            WE->>WE: evaluate expression (safe_eval)
        end

        WE->>WE: update state
    end

    WE->>DB: save execution record
    WE-->>R: final result
    R-->>C: response
```

## RAG Pipeline

```mermaid
flowchart LR
    subgraph "Ingestion"
        A1[Raw Document] --> A2[TextChunker]
        A2 --> A3[EmbeddingService]
        A3 --> A4[Qdrant Collection]
    end

    subgraph "Search"
        B1[User Query] --> B2[Embed Query]
        B2 --> B3[Vector Search]
        B3 --> B4[Retrieved Chunks]
    end

    subgraph "Generation"
        B4 --> C1[Context Assembly]
        C1 --> C2[Prompt Builder]
        C2 --> C3[LLM Call]
        C3 --> C4[Augmented Response]
    end

    subgraph "Documents"
        D1[PDF Upload] --> A1
        D2[Text Upload] --> A1
        D3[Markdown Upload] --> A1
    end
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Load Balancer"
            LB[Reverse Proxy / Load Balancer]
        end

        subgraph "API Cluster"
            API1[API Instance 1]
            API2[API Instance 2]
            API3[API Instance N]
        end

        subgraph "Frontend"
            WEB1[Web Instance 1]
            WEB2[Web Instance N]
        end

        subgraph "Data Services"
            PG[(PostgreSQL<br/>Primary)]
            PGR[(PostgreSQL<br/>Read Replica)]
            RD[(Redis Cluster)]
            QD[(Qdrant)]
        end

        subgraph "Monitoring"
            PROM[Prometheus]
            GRAF[Grafana]
            OTLP[OpenTelemetry<br/>Collector]
        end

        subgraph "External"
            OA[OpenAI API]
            AN[Anthropic API]
            GG[Google API]
        end
    end

    Internet --> LB
    LB --> API1 & API2 & API3
    LB --> WEB1 & WEB2
    API1 & API2 & API3 --> PG
    API1 & API2 & API3 --> PGR
    API1 & API2 & API3 --> RD
    API1 & API2 & API3 --> QD
    API1 & API2 & API3 --> PROM
    API1 & API2 & API3 --> OTLP
    PROM --> GRAF
    API1 & API2 & API3 --> OA & AN & GG
```

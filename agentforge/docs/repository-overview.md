# Repository Overview

## Module Map

```
agentforge/
├── apps/                          # Application packages
│   ├── api/                       # Backend API (FastAPI)
│   │   ├── core/                  # Config, database, security, health, metrics
│   │   ├── routes/                # HTTP route handlers
│   │   ├── services/              # Business logic layer
│   │   ├── middleware/            # Logging, rate limiting, audit
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── dependencies/          # FastAPI dependency injection
│   │   ├── alembic/               # Database migrations
│   │   ├── tools/                 # Tool implementations (future)
│   │   └── websocket/             # WebSocket handlers (future)
│   └── web/                       # Frontend (Next.js 15)
│       ├── app/                   # Next.js App Router pages
│       ├── components/            # React components
│       ├── stores/                # Zustand state management
│       ├── lib/                   # Utility functions
│       └── types/                 # TypeScript type definitions
├── packages/                      # Shared packages
│   ├── agents/                    # Agent orchestration logic
│   ├── llm/                       # LLM provider abstraction
│   │   └── src/                   # Provider factory, OpenAI/Anthropic impl
│   ├── memory/                    # Memory and persistence
│   ├── observability/             # Shared observability primitives
│   ├── rag/                       # RAG pipeline primitives
│   ├── shared/                    # Shared types and utilities
│   ├── tools/                     # Tool definitions
│   │   └── src/                   # ToolRegistry, web_search, calculator
│   └── workflows/                 # Workflow execution engine
│       └── src/                   # SafeEval, WorkflowEngine (LangGraph)
├── infrastructure/                # Deployment and infrastructure
│   ├── docker/                    # Dockerfiles
│   ├── kubernetes/                # Kubernetes manifests (future)
│   └── terraform/                 # Terraform configs (future)
├── tests/                         # Test suite
│   ├── unit/                      # Unit and integration tests
│   ├── e2e/                       # End-to-end tests (future)
│   ├── integration/               # Integration tests (future)
│   └── load/                      # Load tests (future)
├── docs/                          # Documentation
│   ├── diagrams/                  # Architecture diagrams
│   └── *.md                       # All documentation files
├── scripts/                       # Utility scripts
└── .github/                       # GitHub configuration
    ├── workflows/                 # CI/CD workflows
    └── ISSUE_TEMPLATE/            # Issue templates
```

## Package Responsibilities

### `apps/api` — Backend API
The core backend service. FastAPI application with full CRUD for agents, workflows, executions, RAG operations, authentication, and observability.

**Key modules:**
- `core/config.py`: All environment configuration via Pydantic Settings
- `core/database.py`: Async SQLAlchemy engine and session management
- `core/security.py`: JWT token creation/verification, password hashing
- `core/health.py`: Health check system (database, Redis, Qdrant)
- `core/metrics.py`: Prometheus metrics (HTTP, workflows, agents, RAG)
- `core/telemetry.py`: OpenTelemetry tracing (FastAPI, HTTPX, SQLAlchemy)
- `core/exceptions.py`: Structured error handling with global handlers
- `core/resilience.py`: Circuit breakers (pybreaker) and retry (tenacity)
- `core/logging.py`: Structured logging with structlog
- `services/__init__.py`: AgentService, WorkflowService, ExecutionService
- `services/audit.py`: Audit logging service
- `services/rag.py`: RAG pipeline (ingestion, search, augmentation)
- `services/vector_store.py`: Qdrant vector store with lazy init
- `middleware/rate_limit.py`: In-memory rate limiting for auth/upload
- `middleware/audit.py`: Automatic CRUD audit logging
- `middleware/logging.py`: Request/response structured logging

### `apps/web` — Frontend UI
Next.js 15 application with App Router, Tailwind CSS, and Zustand state management.

**Pages:** Login, Agents (list + detail), Workflows (list + detail), Observability, Settings
**Stores:** agent-store, workflow-store

### `packages/llm` — LLM Provider Abstraction
Abstract `LLMProvider` base class with concrete implementations:
- `OpenAIProvider`: GPT-4, GPT-4o, GPT-3.5-turbo
- `AnthropicProvider`: Claude 3.5 Sonnet, Claude 3 Opus
- `get_llm()`: Factory function that returns provider based on config

### `packages/workflows` — Workflow Engine
LangGraph-based workflow execution:
- `WorkflowEngine`: Executes directed graphs of LLM, tool, and condition nodes
- `safe_eval()`: AST-based expression evaluator for condition nodes
- `WorkflowState`: Typed state management with LangGraph

### `packages/tools` — Tool Registry
- `ToolRegistry`: Central registry for available tools
- Tools: `web_search`, `calculator`, `current_datetime`

## Service Ownership

| Service | Owner | Responsibility |
|---|---|---|
| `AgentService` | API | CRUD for agents, tenant isolation |
| `WorkflowService` | API | CRUD for workflows, tenant isolation |
| `ExecutionService` | API | Execution records, metrics queries |
| `AuditService` | API | Audit log creation and querying |
| `RAGPipeline` | API | Document ingest, search, augment |
| `VectorStoreService` | API | Qdrant interactions, embedding |
| `LLMProvider` | Packages | Multi-provider LLM abstraction |
| `WorkflowEngine` | Packages | LangGraph execution, safe eval |
| `ToolRegistry` | Packages | Tool registration and execution |

## Extension Points

The platform is designed for extensibility at several points:

### 1. New LLM Providers
Add a new provider in `packages/llm/src/__init__.py`:
```python
class CustomProvider(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implementation
```

### 2. New Tools
Add tools in `packages/tools/src/__init__.py`:
```python
@tool_registry.register("my_tool")
async def my_tool(param: str) -> str:
    """Tool description."""
    return result
```

### 3. New Agent Types
Extend `AgentService` and create route handlers for new agent behaviors.

### 4. New Storage Backends
Implement the vector store interface for alternatives to Qdrant (e.g., Pinecone, Weaviate).

### 5. New Middleware
Add middleware by implementing `BaseHTTPMiddleware` and registering in `main.py`.

### 6. New RAG Strategies
Extend `RAGPipeline` with alternative retrieval strategies (HyDE, multi-query, reranking).

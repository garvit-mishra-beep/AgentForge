# AgentForge AI — System Design

## 1. Overview

AgentForge AI is a multi-tenant SaaS platform for building, deploying, and monitoring AI agents. This document covers the detailed system design, component responsibilities, data models, and scaling strategy.

## 2. Component Architecture

### 2.1 Frontend (`apps/web`)

Next.js 15 application using the App Router.

**Key Pages:**
- `/` — Landing / dashboard
- `/agents` — List and manage agents
- `/agents/new` — Agent builder wizard
- `/agents/[id]` — Agent detail, config, logs
- `/workflows` — Workflow list
- `/workflows/[id]` — Workflow editor (React Flow)
- `/observability` — Dashboard with charts
- `/evaluations` — Evaluation suites
- `/settings` — API keys, team, billing

**State Management:**
- Zustand for global UI state
- React Query (`@tanstack/react-query`) for server data
- Server Actions for mutations where applicable

**Component Library:**
- shadcn/ui (Radix primitives + TailwindCSS)
- React Flow for workflow editor
- Recharts for dashboard visualizations

### 2.2 API Gateway (`apps/api`)

FastAPI application with the following route groups:

```
/api/v1/
├── agents/           # CRUD for agents
│   ├── :id/invoke    # Execute agent
│   ├── :id/stream    # Streaming execution
│   └── :id/versions  # Version management
├── workflows/        # CRUD for workflows
│   ├── :id/execute   # Execute workflow
│   └── :id/versions
├── tools/            # Tool registry
├── memory/           # Memory management
├── rag/              # Document management & search
├── executions/       # Execution history & logs
├── observability/    # Metrics & traces
├── evaluations/      # Eval suites
├── api-keys/         # API key management
└── auth/             # Clerk webhooks, user management
```

**Middleware Stack:**
1. Clerk JWT verification
2. Rate limiting (Redis-backed sliding window)
3. Request logging (OpenTelemetry)
4. Error handler (structured error responses)
5. CORS

### 2.3 Agent Manager

The core abstraction that manages agent lifecycles.

```
AgentManager
├── create(config: AgentConfig) -> Agent
├── invoke(agent_id, input, context) -> Response
├── stream(agent_id, input, context) -> Stream[Chunk]
├── get_state(execution_id) -> ExecutionState
└── cancel(execution_id)
```

### 2.4 Workflow Engine (LangGraph)

Each workflow is compiled into a LangGraph `StateGraph`. The engine:

1. **Compiles** the visual workflow into a LangGraph graph definition
2. **Checkpoints** state after each node (via PostgreSQL or memory)
3. **Handles branching** based on conditional edge rules
4. **Retries** failed nodes up to configured limit
5. **Emits telemetry** for each node invocation

### 2.5 Tool Executor

Sandboxed tool execution environment:

- Built-in tools: web search, code sandbox, HTTP client, file reader
- Custom tools: user-defined via OpenAPI spec or inline JavaScript/Python
- Rate limiting per tool per tenant
- Timeout enforcement per tool invocation

### 2.6 Memory Manager

```
MemoryManager
├── short_term: Redis-based ring buffer (last N turns)
├── long_term: Qdrant-based vector recall
└── user_memory: Key-value store for persistent user facts
```

## 3. Data Models

### 3.1 Agent

```json
{
  "id": "uuid",
  "name": "Customer Support Agent",
  "slug": "customer-support",
  "description": "Handles customer inquiries",
  "model_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0
  },
  "system_prompt": "You are a helpful support agent...",
  "tools": ["web_search", "code_sandbox"],
  "memory_config": {
    "type": "short_term",
    "turns": 20
  },
  "version": 3,
  "status": "active",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### 3.2 Workflow

```json
{
  "id": "uuid",
  "name": "Research & Summarize",
  "nodes": [
    { "id": "n1", "type": "agent", "agent_id": "...", "config": {} },
    { "id": "n2", "type": "condition", "expression": "output.complete == true" },
    { "id": "n3", "type": "agent", "agent_id": "...", "config": {} }
  ],
  "edges": [
    { "from": "n1", "to": "n2" },
    { "from": "n2", "to": "n3", "condition": "true" },
    { "from": "n2", "to": "__end__", "condition": "false" }
  ],
  "version": 2,
  "status": "published"
}
```

### 3.3 Execution

```json
{
  "id": "uuid",
  "agent_id": "uuid",
  "workflow_id": "uuid | null",
  "input": { "message": "Hello" },
  "output": { "reply": "Hi there!" },
  "status": "completed",
  "steps": [
    {
      "node": "agent_1",
      "llm_calls": 2,
      "tokens_in": 450,
      "tokens_out": 120,
      "duration_ms": 2340,
      "tool_calls": [
        { "tool": "web_search", "duration_ms": 800, "result_summary": "..." }
      ],
      "started_at": "ISO8601",
      "completed_at": "ISO8601"
    }
  ],
  "total_tokens": 570,
  "total_cost_usd": 0.0085,
  "duration_ms": 3400,
  "error": null,
  "created_at": "ISO8601"
}
```

### 3.4 Tool Registry

```json
{
  "id": "uuid",
  "type": "builtin|custom",
  "name": "web_search",
  "description": "Search the web for information",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string" }
    },
    "required": ["query"]
  },
  "config": {
    "provider": "tavily",
    "api_key_ref": "encrypted_storage"
  }
}
```

## 4. Database Schema (PostgreSQL)

```sql
-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    model_config JSONB NOT NULL,
    system_prompt TEXT,
    tools JSONB DEFAULT '[]',
    memory_config JSONB DEFAULT '{"type": "short_term", "turns": 20}',
    version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

-- Workflows
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,
    version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Executions
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    agent_id UUID REFERENCES agents(id),
    workflow_id UUID REFERENCES workflows(id),
    input JSONB,
    output JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    steps JSONB DEFAULT '[]',
    total_tokens INT DEFAULT 0,
    total_cost_usd DECIMAL(12,6) DEFAULT 0,
    duration_ms INT DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255),
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,
    permissions JSONB DEFAULT '["agent:invoke"]',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_executions_tenant ON executions(tenant_id, created_at DESC);
CREATE INDEX idx_executions_agent ON executions(agent_id, created_at DESC);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_agents_tenant ON agents(tenant_id, slug);
```

## 5. Scaling Strategy

### 5.1 Horizontal Scaling

| Component | Strategy | Notes |
|-----------|----------|-------|
| FastAPI | Multiple workers behind ALB | Stateless, shared PostgreSQL |
| Next.js | Serverless (Vercel) or container | ISR for static pages |
| Redis | ElastiCache cluster | Session, rate limiting, queue |
| Qdrant | Distributed deployment | Replication factor 3 |
| PostgreSQL | Read replicas, connection pooling | PgBouncer recommended |

### 5.2 Caching Strategy

| Data | Cache | TTL | Invalidation |
|------|-------|-----|-------------|
| Agent config | Redis | 5 min | On agent update |
| Workflow definition | Redis | 5 min | On workflow publish |
| LLM responses | Redis (optional) | 1 hour | Exact input hash |
| User session | Redis | Session duration | Logout |

### 5.3 Rate Limiting

- Tenant-level: 1000 req/min (configurable)
- Agent-level: 100 req/min (configurable)
- Token-based: Burst limit per API key
- Implementation: Redis sorted set (sliding window)

## 6. Security Design

| Concern | Implementation |
|---------|---------------|
| Auth | Clerk-managed JWT + API keys |
| Encryption at rest | PostgreSQL TDE, Qdrant encryption |
| Encryption in transit | TLS 1.3 everywhere |
| Secrets management | Encrypted at DB level, Vault for production |
| Tool sandboxing | gVisor / Firecracker for code execution |
| Rate limiting | Redis-backed per-tenant |
| Audit logging | All API mutations logged |
| Data isolation | Tenant ID on every row, RLS policies |

## 7. Monitoring & Observability

### OpenTelemetry Signals

| Signal | Source | Exporter |
|--------|--------|---------|
| Traces | FastAPI middleware, LangGraph hooks | OTLP → Prometheus |
| Metrics | request count, latency, token usage | OTLP → Prometheus |
| Logs | Python logging, structured JSON | Filebeat → Loki |

### Key Dashboards (Grafana)

1. **Platform Overview:** Requests/sec, error rate, P50/P95/P99 latency
2. **LLM Usage:** Tokens per provider, cost per agent, model breakdown
3. **Agent Performance:** Success rate, avg duration, tool call frequency
4. **Tenant Health:** Rate limit hits, error breakdown, active agents

## 8. Disaster Recovery

| Scenario | RTO | RPO | Strategy |
|----------|-----|-----|----------|
| Single instance failure | < 1 min | 0 | ALB + auto-scaling group |
| AZ outage | < 5 min | < 1 min | Multi-AZ deployment |
| Database corruption | < 1 hour | < 5 min | Point-in-time recovery |
| Full region failure | < 4 hours | < 15 min | Cross-region replication |

# API Reference

## Authentication

### `POST /api/v1/auth/token`
Authenticate and receive JWT tokens.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Rate Limited:** 100 requests per 60 seconds.

### `POST /api/v1/auth/refresh`
Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### `POST /api/v1/auth/register`
Create a new user account.

**Request:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Rate Limited:** 10 requests per 3600 seconds.

### `POST /api/v1/auth/logout`
Logout by providing your current token.

**Request:**
```json
{
  "token": "string"
}
```

## Agents

### `POST /api/v1/agents`
Create a new agent.

**Request:**
```json
{
  "name": "My Agent",
  "slug": "my-agent",
  "description": "A helpful agent",
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  },
  "system_prompt": "You are a helpful assistant.",
  "tools": ["web_search", "calculator"],
  "memory_config": {"type": "buffer", "k": 10}
}
```

### `GET /api/v1/agents`
List all agents for the current tenant.

**Query Parameters:**
- `status` (optional) — Filter by status
- `skip` (default: 0) — Pagination offset
- `limit` (default: 20, max: 100) — Page size

### `GET /api/v1/agents/{id}`
Get agent details.

### `PUT /api/v1/agents/{id}`
Update agent configuration.

### `DELETE /api/v1/agents/{id}`
Delete an agent.

### `POST /api/v1/agents/{id}/invoke`
Invoke an agent with a message.

**Request:**
```json
{
  "message": "Hello, what can you do?"
}
```

## Workflows

### `POST /api/v1/workflows`
Create a new workflow.

**Request:**
```json
{
  "name": "Customer Support",
  "description": "Handle customer inquiries",
  "definition": {
    "nodes": [
      {"id": "start", "type": "trigger"},
      {"id": "classify", "type": "llm", "config": {"prompt": "Classify..."}},
      {"id": "respond", "type": "llm", "config": {"prompt": "Respond..."}}
    ],
    "edges": [
      {"from": "start", "to": "classify"},
      {"from": "classify", "to": "respond"}
    ]
  }
}
```

### `GET /api/v1/workflows`
List workflows for the current tenant.

### `GET /api/v1/workflows/{id}`
Get workflow details.

### `PUT /api/v1/workflows/{id}`
Update workflow definition.

### `DELETE /api/v1/workflows/{id}`
Delete a workflow.

## Executions

### `GET /api/v1/executions`
List executions.

**Query Parameters:**
- `status` (optional) — Filter by status
- `agent_id` (optional) — Filter by agent
- `workflow_id` (optional) — Filter by workflow
- `skip` (default: 0) — Pagination offset
- `limit` (default: 20, max: 100) — Page size

### `GET /api/v1/executions/{id}`
Get execution details and step-by-step trace.

## RAG

### `POST /api/v1/rag/ingest`
Ingest text content into the vector store.

**Request:**
```json
{
  "content": "Text content to index...",
  "metadata": {"source": "documentation", "category": "api"}
}
```

### `POST /api/v1/rag/upload`
Upload a file for processing. Supported types: PDF, TXT, MD.

**Rate Limited:** 20 requests per 60 seconds.

### `POST /api/v1/rag/search`
Search the vector store.

**Request:**
```json
{
  "query": "What is the API endpoint for...",
  "top_k": 5,
  "threshold": 0.7
}
```

### `POST /api/v1/rag/augment`
Retrieve context and generate an LLM-augmented response.

### `DELETE /api/v1/rag/documents/{id}`
Delete a document from the vector store.

### `GET /api/v1/rag/documents/{id}/stats`
Get document statistics (chunk count, total tokens, etc.).

## Observability

### `GET /api/v1/observability/usage`
Get execution usage metrics.

**Query Parameters:**
- `days` (default: 7, max: 90) — Lookback period
- `agent_id` (optional) — Filter by agent

### `GET /api/v1/health`
Full health check (database, Redis, Qdrant).

**Response:** `200 OK`
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-01-01T00:00:00Z",
  "environment": "development",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"},
    "qdrant": {"status": "ok"}
  }
}
```

### `GET /api/v1/ready`
Readiness probe (checks database only).

### `GET /api/v1/live`
Liveness probe (process-level).

### `GET /metrics`
Prometheus metrics endpoint (text format).

## WebSocket

### `ws://host/ws/executions/{execution_id}`
Subscribe to real-time execution updates.

### `ws://host/ws/events`
Subscribe to general platform events.

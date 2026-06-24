# System Design

## API Design

### Base URL
All API endpoints are prefixed with `/api/v1`.

### Authentication
- **JWT Bearer Tokens**: Access tokens (30 min) + Refresh tokens (7 days)
- **API Keys**: Hash-based authentication for programmatic access
- **Headers**: `Authorization: Bearer <token>` or `X-API-Key: <key>`

### Standard Responses

**Success:**
```json
{
  "id": "uuid",
  "name": "resource name",
  "created_at": "2025-01-01T00:00:00Z",
  ...
}
```

**Error:**
```json
{
  "error": "ERROR_CODE",
  "detail": "Human-readable message",
  "status_code": 400
}
```

**Paginated:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

## Database Schema

```mermaid
erDiagram
    User {
        uuid id PK
        string username UK
        string email UK
        string password_hash
        uuid tenant_id
        boolean is_active
        boolean is_superadmin
        jsonb metadata
        datetime created_at
        datetime updated_at
    }
    
    Agent {
        uuid id PK
        uuid tenant_id FK
        string name
        string slug UK
        text description
        jsonb llm_config
        text system_prompt
        jsonb tools
        jsonb memory_config
        int version
        string status
        datetime created_at
        datetime updated_at
    }
    
    Workflow {
        uuid id PK
        uuid tenant_id FK
        string name
        text description
        jsonb definition
        int version
        string status
        datetime created_at
        datetime updated_at
    }
    
    Execution {
        uuid id PK
        string external_id UK
        uuid tenant_id FK
        uuid agent_id FK
        uuid workflow_id FK
        string type
        jsonb input
        jsonb output
        string status
        float duration_ms
        int total_tokens
        float cost_usd
        jsonb metadata
        datetime created_at
        datetime updated_at
    }
    
    APIKey {
        uuid id PK
        uuid tenant_id FK
        string name
        string key_hash UK
        jsonb permissions
        datetime expires_at
        datetime last_used_at
        datetime created_at
    }
    
    AuditLog {
        uuid id PK
        uuid actor_id FK
        uuid tenant_id FK
        string action
        string resource_type
        string resource_id
        jsonb meta_data
        string ip_address
        datetime created_at
    }
    
    User ||--o{ Agent : "has"
    User ||--o{ Workflow : "has"
    User ||--o{ Execution : "has"
    User ||--o{ APIKey : "has"
    User ||--o{ AuditLog : "has"
    Agent ||--o{ Execution : "invoked"
    Workflow ||--o{ Execution : "executed"
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant A as Auth
    participant R as Route
    participant S as Service
    participant D as Database
    participant LLM as LLM

    C->>M: HTTP Request
    M->>M: LoggingMiddleware (log)
    M->>M: RateLimitMiddleware (check)
    M->>A: AuthMiddleware (verify JWT)
    A->>M: User payload
    M->>A: AuditMiddleware (log)
    A->>R: Forward to route handler
    R->>R: Validate input (Pydantic)
    R->>S: Call service method
    S->>D: Query/insert (SQLAlchemy)
    D-->>S: Result
    S->>LLM: Call LLM (if needed)
    LLM-->>S: Response
    S-->>R: Return data
    R-->>A: JSON response
    M->>M: MetricsMiddleware (track)
    M-->>C: HTTP Response
```

## Security Architecture

See [security.md](security.md) for detailed security documentation.

### Key Security Measures
- **JWT**: Signed with HS256, includes jti, exp, iss, aud claims
- **Password Hashing**: bcrypt with salt
- **API Keys**: SHA-256 hashed storage, never stored in plaintext
- **Expression Safety**: AST-based `safe_eval()` prevents arbitrary code execution
- **Rate Limiting**: Per-IP, per-route with configurable windows
- **Input Validation**: Pydantic schemas reject malformed data at boundary
- **Tenant Isolation**: All queries filtered by `tenant_id`
- **Audit Logging**: CRUD operations logged with actor, resource, timestamp

## Error Handling

```
Exception Hierarchy:
├── AppException (base)
│   ├── NotFoundException (404)
│   ├── AuthenticationException (401)
│   ├── RateLimitException (429)
│   └── ValidationException (422)
└── Exception (500 — generic fallback)
```

All exceptions are caught by global handlers in `register_exception_handlers()` and return structured JSON error responses.

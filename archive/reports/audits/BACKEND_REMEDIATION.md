# Pillar 1: Backend Remediation Plan

This remediation plan lists the required fixes for the AgentForge backend in order of severity (highest priority first).

---

## Remediation Tasks

### 1. Fix HTTP Middleware Stack Registration Order
- **Finding ID**: Middleware Stack Order
- **Severity**: P0 (Critical)
- **File**: [apps/api/app/main.py](file:///c:/Users/garvi/AgentForge/apps/api/app/main.py#L188-L191)
- **Remediation**:
  Re-order middleware registrations so CORS and Correlation ID middlewares are registered *last* (which means they execute *first* on inbound requests):
  ```python
  # Added in this order: Executes first to last: CORS -> Correlation -> Security Headers -> Rate Limit -> Auth
  app.middleware("http")(auth_middleware)
  app.middleware("http")(rate_limit_middleware)
  app.middleware("http")(security_headers_middleware)
  app.middleware("http")(correlation_middleware)
  # CORSMiddleware is added via app.add_middleware() which runs outside the custom HTTP stack
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None. Apply immediately.

---

### 2. Implement Unique Sorted Set Members in Rate Limiter
- **Finding ID**: Rate Limiter: ZSET Collisions
- **Severity**: P0 (Critical)
- **File**: [apps/api/core/redis.py](file:///c:/Users/garvi/AgentForge/apps/api/core/redis.py#L162)
- **Remediation**:
  Ensure that each sorted set entry has a unique member string by appending a random UUID or millisecond component:
  ```python
  member_id = f"{now}:{uuid.uuid4().hex}"
  await r.zadd(key, {member_id: now})
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 3. Enforce require_user on Code Review Endpoint
- **Finding ID**: Route: POST /api/v1/review
- **Severity**: P1 (High)
- **File**: [apps/api/app/routes/review.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/review.py#L235-L241)
- **Remediation**:
  Change the `user_id` route parameter to be explicitly required and injected:
  ```python
  user_id: str = Depends(require_user)
  ```
  Ensure all subsequent processing context functions (such as `_process_review`) use this validated user ID.
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 4. Secure Concurrent JWT Refresh Requests
- **Finding ID**: JWT: Unprotected Concurrent Token Refresh
- **Severity**: P1 (High)
- **File**: [apps/api/app/routes/auth.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/auth.py#L124-L150)
- **Remediation**:
  Acquire a row-level lock (`SELECT FOR UPDATE`) on the `refresh_tokens` record inside a database transaction block before rotating or revoking tokens:
  ```python
  async with db.transaction() as conn:
      active = await conn.fetchval(
          "SELECT 1 FROM refresh_tokens WHERE jti = $1 AND user_id = $2 AND revoked = FALSE AND expires_at > NOW() FOR UPDATE",
          old_jti, user_id
      )
  ```
- **Estimated Effort**: M (Medium)
- **Dependencies**: None.

---

### 5. Fail Fast on Missing Encryption Key Config
- **Finding ID**: Key Security: Ephemeral Encryption Key Leakage
- **Severity**: P1 (High)
- **File**: [apps/api/core/config.py](file:///c:/Users/garvi/AgentForge/apps/api/core/config.py#L117-L122)
- **Remediation**:
  Throw a startup `ValueError` during settings validation if `AGENTFORGE_ENCRYPTION_KEY` is empty while `auth_enabled` is active, rather than falling back to an ephemeral key.
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 6. Acquire PG Advisory Lock for Schema Migrations
- **Finding ID**: Migrations: Scale-out Migration Concurrency Race
- **Severity**: P1 (High)
- **File**: [apps/api/core/database.py](file:///c:/Users/garvi/AgentForge/apps/api/core/database.py#L60-L77)
- **Remediation**:
  Wrap the migration script check and execution in a session-level PostgreSQL advisory lock so concurrent container bootups wait for the migration runner to complete:
  ```python
  # Acquire advisory lock 145293
  await conn.execute("SELECT pg_advisory_xact_lock(145293);")
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 7. Define Pydantic Input Schemas for Memory Routes
- **Finding ID**: Route: POST /api/v1/memories
- **Severity**: P2 (Medium)
- **File**: [apps/api/app/routes/memories.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/memories.py#L83-L123)
- **Remediation**:
  Create `MemoryCreate` and `MemoryUpdate` Pydantic models in `models/schemas.py`. Update memory route handlers to accept these schemas as type-hinted request bodies.
- **Estimated Effort**: M (Medium)
- **Dependencies**: None.

---

### 8. Add ON DELETE CASCADE to User Relationships
- **Finding ID**: Schema: Missing ON DELETE cascades
- **Severity**: P2 (Medium)
- **File**: [apps/api/migrations/001_initial.sql](file:///c:/Users/garvi/AgentForge/apps/api/migrations/001_initial.sql)
- **Remediation**:
  Write an additive migration script (e.g. `022_add_on_delete_cascade.sql`) to drop the existing foreign key constraints on `teams.created_by` and `tasks.created_by` and re-add them with `ON DELETE CASCADE`.
- **Estimated Effort**: M (Medium)
- **Dependencies**: Fix 6 (PG Advisory Lock) should be implemented first to ensure migrations run safely.

---

### 9. Propagate Correlation ID to Background Tasks
- **Finding ID**: Tracing: Correlation ID Not Propagated
- **Severity**: P2 (Medium)
- **File**: [apps/api/app/routes/tasks.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/tasks.py#L91)
- **Remediation**:
  Capture `request.state.correlation_id` in the API handler and pass it into the background worker queue or LangGraph state context dictionary, ensuring it's available in all node execution logs.
- **Estimated Effort**: M (Medium)
- **Dependencies**: None.

---

### 10. Register CorrelationFilter in Logging Configuration
- **Finding ID**: Observability: Unregistered CorrelationFilter
- **Severity**: P3 (Low)
- **File**: [apps/api/core/logging_config.py](file:///c:/Users/garvi/AgentForge/apps/api/core/logging_config.py#L24-L38)
- **Remediation**:
  Instantiate and register the `CorrelationFilter` on standard console output stream handlers during log setup:
  ```python
  handler.addFilter(CorrelationFilter(lambda: getattr(context, "correlation_id", None)))
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

# Pillar 1: Backend Audit Report

This report documents the findings from a deep technical audit of the AgentForge backend (`apps/api/`).

---

## Summary Table

| Severity | Count | Status |
|----------|-------|--------|
| **P0 (Critical)** | 2 | ❌ Action Required |
| **P1 (High)** | 4 | ❌ Action Required |
| **P2 (Medium)** | 3 | ⚠️ Remediation Recommended |
| **P3 (Low)** | 1 | ℹ️ Minor Polish |
| **TOTAL** | 10 | ❌ **NOT READY** |

---

## 1.1 API Layer

### Route: POST /api/v1/review
- **File**: [apps/api/app/routes/review.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/review.py#L235-L284)
- **Severity**: P1 (High)
- **Finding**: Route fails to use the `require_user` dependency, allowing `user_id` to remain `None` and default to `DEMO_USER_ID`.
- **Impact**: Any authenticated user's submitted code reviews are recorded under the public `DEMO_USER_ID`, bypassing tenant isolation and preventing the use of their private BYOK keys during analysis.
- **Proof**:
  ```python
  @router.post("", response_model=ReviewResponse)
  async def submit_review(
      request: ReviewRequest,
      http_request: Request,
      user_id: str | None = None,  # Will be set by dependency or default to demo
      db: AsyncSession = Depends(get_db),
  ):
  ```
- **Fix**: Update the parameter to inject the user dependency: `user_id: str = Depends(require_user)`.

---

### Route: POST /api/v1/memories and PUT /api/v1/memories/{memory_id}
- **File**: [apps/api/app/routes/memories.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/memories.py#L83-L123)
- **Severity**: P2 (Medium)
- **Finding**: Raw request JSON is parsed dynamically using `await request.json()` instead of being validated through a typed Pydantic schema.
- **Impact**: Missing request fields will cause unhandled `KeyError` exceptions leading to 500 Internal Server Errors instead of 400 Bad Request responses. Unbounded payload size exposes the endpoint to memory exhaustion.
- **Proof**:
  ```python
  @router.post("", status_code=201)
  async def create_memory(
      request: Request,
      user_id: str = Depends(require_user),
  ):
      db = _db(request)
      body = await request.json()
      mem_id = await store_memory(
          db, user_id,
          key=body["key"], # KeyError if "key" missing
          content=body["content"],
          ...
      )
  ```
- **Fix**: Define `MemoryCreate` and `MemoryUpdate` Pydantic schemas and enforce them as route parameter inputs.

---

## 1.2 Authentication & Authorization

### JWT: Unprotected Concurrent Token Refresh
- **File**: [apps/api/app/routes/auth.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/auth.py#L124-L150)
- **Severity**: P1 (High)
- **Finding**: Token refresh state check (`refresh_token_active`) and revocation mutation (`revoke_refresh_token`) run non-atomically without a transaction block or row lock.
- **Impact**: Race conditions occur when concurrent refresh requests arrive. Multiple new access/refresh token pairs can be minted for the same old token, violating single-use rotation guarantees.
- **Proof**:
  ```python
  if not await refresh_token_active(db, old_jti, user_id):
      raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

  new_token = create_token(user_id)
  new_refresh, new_jti, expires_at = create_refresh_token(user_id)
  await store_refresh_token(db, new_jti, user_id, expires_at)
  await revoke_refresh_token(db, old_jti, replaced_by=new_jti)
  ```
- **Fix**: Wrap the validation and update steps inside a `SELECT FOR UPDATE` or run them inside an atomic `db.transaction()` block.

---

### Key Security: Ephemeral Encryption Key Leakage
- **File**: [apps/api/core/encryption.py](file:///c:/Users/garvi/AgentForge/apps/api/core/encryption.py#L13-L25)
- **Severity**: P1 (High)
- **Finding**: Ephemeral AES encryption key is generated automatically in-memory when the `AGENTFORGE_ENCRYPTION_KEY` environment variable is not defined.
- **Impact**: Encrypted API keys written to PostgreSQL become permanently unrecoverable once the container/server restarts, resulting in persistent decryption failures and breaking LLM agent workflows.
- **Proof**:
  ```python
  else:
      self.key = AESGCM.generate_key(bit_length=256)
      logger.warning(
          "No AGENTFORGE_ENCRYPTION_KEY set. Generated ephemeral key. "
          "Keys encrypted with this key will be unrecoverable after restart."
      )
  ```
- **Fix**: Force the application to fail fast on startup if `AGENTFORGE_ENCRYPTION_KEY` is not configured and `auth_enabled=True`.

---

## 1.3 Agent Orchestration

### Tracing: Correlation ID Not Propagated to Agent Executions
- **File**: [apps/api/app/routes/tasks.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/tasks.py#L91)
- **Severity**: P2 (Medium)
- **Finding**: The background worker processes spawned via the `tracker` do not receive the client request's `correlation_id` header or carry it through thread local states.
- **Impact**: Background agent execution logs and subsequent LLM API calls cannot be correlated with the API request that triggered them, breaking full-system tracing.
- **Proof**:
  ```python
  tracker.create_task(run_task(db, task_id), name=f"task-{task_id[:8]}")
  ```
- **Fix**: Propagate `correlation_id` through the state dictionary passed into the LangGraph state machine.

---

## 1.4 Database Layer

### Migrations: Scale-out Migration Concurrency Race
- **File**: [apps/api/core/database.py](file:///c:/Users/garvi/AgentForge/apps/api/core/database.py#L60-L77)
- **Severity**: P1 (High)
- **Finding**: Database migration script executes sequentially in startup lifespan hooks without any locking mechanism to prevent parallel execution.
- **Impact**: If multiple API containers scale out concurrently (e.g. on Railway, Kubernetes), they will check `schema_migrations` simultaneously, find pending migrations, and execute the migration DDL statements in parallel, causing table lock conflicts or duplicate execution failures.
- **Proof**:
  ```python
  async with self.pool.acquire() as conn:
      for mf in migration_files:
          already_run = await conn.fetchval(
              "SELECT COUNT(*) FROM schema_migrations WHERE filename = $1",
              mf.name,
          )
          if already_run:
              continue
          sql = mf.read_text()
          async with conn.transaction():
              await conn.execute(sql)
  ```
- **Fix**: Acquire a PostgreSQL advisory lock (e.g., `SELECT pg_advisory_xact_lock(145293);`) at the start of the `run_migrations` transaction block.

---

### Schema: Missing ON DELETE cascades in Initial Schema
- **File**: [apps/api/migrations/001_initial.sql](file:///c:/Users/garvi/AgentForge/apps/api/migrations/001_initial.sql#L19-L65)
- **Severity**: P2 (Medium)
- **Finding**: Critical foreign keys lack ON DELETE actions (referencing `users(id)`).
- **Impact**: Deleting a user account will fail with foreign key constraint violation errors as child records in the `teams` and `tasks` tables cannot be handled automatically.
- **Proof**:
  ```sql
  CREATE TABLE IF NOT EXISTS teams (
      ...
      created_by  UUID NOT NULL REFERENCES users(id) -- missing ON DELETE action
  );
  ```
- **Fix**: Define `ON DELETE CASCADE` on all foreign key constraints.

---

## 1.5 Redis Layer

### Rate Limiter: Rate Limit Bypass in ZSET Collisions
- **File**: [apps/api/core/redis.py](file:///c:/Users/garvi/AgentForge/apps/api/core/redis.py#L162)
- **Severity**: P0 (Critical)
- **Finding**: The sliding window rate limit checks write elements using `str(int(now))` as the ZSET member name, which has second-level precision.
- **Impact**: Requests occurring in the same second result in key collisions and overwrite the existing sorted set member rather than inserting a new one. A client can bypass the rate limiter by burst-transmitting hundreds of requests per second, which will only count as 1 request.
- **Proof**:
  ```python
  await r.zadd(key, {str(int(now)): now})
  ```
- **Fix**: Use millisecond-level precision or combine the timestamp with a unique UUID string for the member names to avoid collisions: `f"{now}:{uuid.uuid4().hex}"`.

---

## 1.6 Middleware Stack

### Middleware Stack Order: CORS & Security Headers Bypass
- **File**: [apps/api/app/main.py](file:///c:/Users/garvi/AgentForge/apps/api/app/main.py#L188-L191)
- **Severity**: P0 (Critical)
- **Finding**: The HTTP middleware stack is registered such that `auth_middleware` executes first and returns an early `JSONResponse(status_code=401)` on failure, bypassing downstream middlewares.
- **Impact**: CORSMiddleware, correlation ID logging, rate limiting, and security headers are never executed for unauthenticated requests. Unauthenticated API calls return 401 without CORS headers (causing browser blockages) and without security protection headers.
- **Proof**:
  ```python
  # Added in this order: CORSMiddleware -> correlation -> rate_limit -> security_headers -> auth
  # Executed in reverse order: auth -> security_headers -> rate_limit -> correlation -> CORS
  app.middleware("http")(correlation_middleware)
  app.middleware("http")(rate_limit_middleware)
  app.middleware("http")(security_headers_middleware)
  app.middleware("http")(auth_middleware)
  ```
- **Fix**: Reverse the registration order so that CORS and Correlation middlewares run first in the request-handling lifecycle.

---

### Observability: Unregistered CorrelationFilter
- **File**: [apps/api/core/logging_config.py](file:///c:/Users/garvi/AgentForge/apps/api/core/logging_config.py#L40-L51)
- **Severity**: P3 (Low)
- **Finding**: `CorrelationFilter` is defined in the logging configuration but is never attached to any handlers in the logging pipeline.
- **Impact**: The generated `correlation_id` is never automatically injected into the logging record fields when standard loggers write entries.
- **Proof**: `CorrelationFilter` is not imported or referenced anywhere outside of `logging_config.py`.
- **Fix**: Instantiate and add `CorrelationFilter` to the root logging handlers in `setup_logging()`.

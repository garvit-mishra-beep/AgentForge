# Reliability Review — AgentForge

## Score: 5/10

---

## 1. Crash / Restart Behavior — ⚠️ 4/10

### What survives a restart:
- PostgreSQL data (persistent)
- Redis data (if Redis is configured and persistent)
- **Nothing else**

### What is lost on restart:
- In-memory review store (all in-flight and completed reviews)
- In-memory rate limit state (rate limit counters reset)
- All `asyncio.create_task` tasks are abandoned (no drain on shutdown)
- Ephemeral encryption key → all encrypted BYOK keys become undecipherable

### Graceful shutdown:
The `lifespan` handler yields and then runs shutdown code:
```python
yield
stop_worker()
await close_redis()
await pool.close()
```
But `stop_worker()` is a no-op. There is no mechanism to:
- Cancel in-flight reviews
- Wait for running agent pipelines
- Drain the work queue
- Store pending state to database

---

## 2. Partial Failure Handling — ⚠️ 5/10

### What happens when components fail:

| Component Failure | Behavior | Graceful? |
|------------------|----------|-----------|
| PostgreSQL down | App fails at startup (`pool.initialize()` raises) | ⚠️ No retry |
| PostgreSQL during runtime | Individual queries raise (caught per-call except orchestrator) | ⚠️ Unhandled in tasks/orchestrator |
| Redis down | Falls back to in-memory (if never connected) or raises on call | ⚠️ |
| Redis mid-operation | `ping()` in init, but no health check during operations — exception in `setex`/`get` would propagate | ❌ |
| Ollama down | `AIProviderError` raised, caught per pipeline, review marked failed | ✅ |
| Any AI provider | Single model retry, then fallback chain, then 503 | ✅ (with caveats) |

### Orchestrator partial failure:
The `run_task` function has no transaction wrapping. If it fails midway:
- Some task_messages are already written to DB
- Execution status is inconsistent (graph_state updated but task not completed)
- No rollback mechanism

---

## 3. Retry Logic — ⚠️ 5/10

### Review pipeline:
- JSON parse failure: 1 retry with stronger prompt instruction
- Model availability: Fallback chain (3 models per role)
- Provider call: 0 retries via `call_with_timeout` → `call_with_retry(retries=0)`

### Agent pipeline:
- Provider call: `call_with_retry(retries=2)` with exponential backoff (1s, 2s)
- Timeout: No retry on timeout (caught by `call_with_timeout`, returns sentinel)

### Gap: **No retry for transient failures**:
- Database connection failures
- Redis connection failures after init
- Network timeouts on provider calls (currently caught as permanent failure)
- No circuit breaker for repeatedly failing providers

---

## 4. Timeout Architecture — ⚠️ 6/10

### Current timeout configuration:
- Agent timeouts: 20s (lead), 30s (builder), 15s (reviewer), 15s (deliver)
- Review pipeline timeouts: 45s (baseline), 30s (builder), 45s (reviewer) — **but defaults unused in some paths**
- Review API poll timeout: 120s (frontend)
- Ollama client timeout: 300s (line 198 in providers.py) — **too high**

### Missing timeouts:
- **Orchestrator streaming**: No timeout on `graph.astream()` — could run forever
- **Database queries**: No query timeout — stuck queries block pool connections
- **Redis operations**: Socket timeout is 2s in init, but individual operations have no timeout
- **Review pipeline total**: No overall timeout — 3 chained model calls could take 2+ minutes

---

## 5. Queue Architecture — ❌ 2/10

### Current state:
There is no queue. `asyncio.create_task` is a fire-and-forget coroutine scheduler, not a queue.

### Problems:
1. No backpressure — unlimited concurrent tasks
2. No ordering guarantees
3. No persistence — all tasks lost on restart
4. No task deduplication — duplicate submissions are not detected
5. No priority queuing
6. No worker health monitoring

### Fix:
Implement a proper work queue with:
- Redis list/stream for persistence
- Consumer groups for multi-worker
- Max queue depth with 503 on overflow
- Task timeout with automatic requeue
- Dead letter queue for failed tasks

---

## 6. Data Integrity — ⚠️ 5/10

### Issues:
1. **Non-atomic review update** (`core/redis.py:79-83`):
   ```python
   async def review_store_update(review_id, data):
       existing = await review_store_get(review_id)
       if existing is not None:
           existing.update(data)
           await review_store_set(review_id, existing)
   ```
   Two concurrent updates → one clobbers the other. With Redis: no transaction/multi. With in-memory: no lock.

2. **Orchestrator partial writes**: Task messages are written individually to DB. If orchestrator fails mid-stream, some messages are committed but the task is marked failed. No rollback.

3. **`_utcnow()` returned local time (FIXED)**: Timestamps were inconsistent across deployments.

---

## 7. Reliability Scorecard

| Category | Score | Key Issue |
|----------|-------|-----------|
| Crash recovery | 4/10 | Lost tasks, ephemeral crypto key |
| Partial failure | 5/10 | No DB transaction in orchestrator |
| Retry logic | 5/10 | No transient failure retry |
| Timeouts | 6/10 | No orchestrator streaming timeout |
| Queue | 2/10 | No queue at all |
| Data integrity | 5/10 | Non-atomic updates |
| Dependency failures | 6/10 | Graceful Redis/Ollama fallback |
| **Overall** | **5/10** | |

---

## 8. Failure Scenarios

### Redis restarts during operation:
1. App has Redis connected → operations proceed normally
2. Redis goes down → next `setex`/`get` raises exception
3. Exception propagates to route handler → 500 error
4. In-memory fallback is NOT activated mid-operation (only at init)
5. **Result**: All review operations fail until app restart

**Fix**: Wrap Redis operations in try/except to switch to in-memory fallback mid-operation.

### Ollama restarts during a review:
1. Baseline model call → connection refused → `AIProviderError`
2. `_run_baseline` raises → caught by pipeline handler → review marked failed
3. No fallback retry for this specific failure (fallback chain only activates at registry.resolve())
4. **Result**: Review fails, user sees error, retries manually
5. **Acceptable** for MVP, but a retry with circuit breaker would be better.

### Database connection pool exhaustion:
1. 10 concurrent requests acquire 10 connections
2. 11th request waits for pool timeout → exception
3. **Result**: Thundering herd — all waiting requests fail

**Fix**: Configure pool timeout and max_waiting. Implement connection pool monitoring.

---

## 9. Recommendations

### Immediate (P0-P1):
1. Add overall timeout to `graph.astream()` in orchestrator
2. Make `review_store_update` atomic (Redis MULTI/EXEC or Lua script)
3. Add try/except around Redis operations for mid-operation failover
4. Implement task tracking for `asyncio.create_task` to enable graceful shutdown

### Short-term (P2):
5. Wrap orchestrator execution in a DB transaction
6. Add circuit breaker for provider calls (3 failures → backoff)
7. Implement proper queue with Redis streams
8. Add query timeouts for database operations

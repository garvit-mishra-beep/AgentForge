# Scalability Review — AgentForge

## Score: 4/10

---

## 1. Multi-Worker Support — ⚠️ 3/10

### Problem: In-memory state prevents horizontal scaling.

The following state is local to each process:
- `_inmem_reviews` (review store fallback)
- `_inmem_rate_limits` (rate limiter fallback)
- `_registry` (ModelRegistry singleton — harmless, same config)
- `_encryption` (EncryptionService singleton — harmless, same key)

**Without Redis**, the system cannot scale beyond 1 worker — review state and rate limits are process-local.

**With Redis**, the review store and rate limiter work across workers, but:
- `asyncio.create_task` is per-worker — submitted reviews are processed only on the worker that received the POST
- If a worker goes down, its in-flight reviews are lost forever
- No mechanism to distribute tasks across workers
- No persistent queue for review submissions

### Fix:
- Make Redis mandatory in production (fail to start if unavailable)
- Use a Redis list or stream as a work queue
- Have each worker consume from the shared queue
- Store task state in Redis for worker-failure recovery

---

## 2. Concurrent User Load — ⚠️ 4/10

### Current limits:
- Review rate limit: 10/hour/IP (hard limit)
- Task/team creation: NO rate limit
- Review concurrency: Effectively unlimited (create_task fires for every submission)
- Ollama model calls: No concurrency limit — N concurrent reviews means N parallel model calls

### Scenario: 100 concurrent users
- Each creates a team → 100 POSTs accepted
- Each submits a review → 100 create_tasks → 300 model calls (baseline + builder + reviewer)
- Ollama with 7B models: ~1-2 req/s per GPU → queue builds up instantly
- Memory: 300 ChatResponse objects + review store entries
- No backpressure — all 100 requests are accepted, most time out or fail

### Fix:
1. Remove `review_max_concurrent` and `review_queue_maxsize` from config (currently unused) and implement them
2. Add a proper work queue (Redis list with consumer groups)
3. Implement backpressure: return 503 when queue depth exceeds limit
4. Add concurrency limiter per-model (max N concurrent calls to the same model)

---

## 3. Database Scaling — ⚠️ 5/10

### Current design:
- Single PostgreSQL with connection pool (2-10 connections)
- Migrations run every startup (idempotent but wasteful at scale)
- N+1 queries in `list_teams` and `list_tasks` (O(n) queries for n items)
- No pagination on most list endpoints (hard LIMIT of 50-100)
- No read replicas
- No query optimization for large datasets

### N+1 Query Example (`routes/teams.py:86-98`):
```python
rows = await db.fetch("SELECT id FROM teams WHERE created_by = $1", user_id)
teams = []
for row in rows:
    team = await _get_team_by_id(db, row["id"], user_id)  # N queries
```

With 1000 teams, this is 1001 queries.

### Fix:
- Use JOIN queries instead of N+1 pattern
- Add cursor-based pagination to all list endpoints
- Cache frequently-accessed data (team members, task lists)

---

## 4. Memory — ⚠️ 4/10

### Unbounded memory growth points:
1. `_inmem_reviews` dict — stores all review data until TTL (3600s). Under 1000 reviews/hour, this is ~500MB
2. `_inmem_rate_limits` dict — one entry per request per IP. Under high load, this grows without bounds
3. In-memory review history (frontend) — last 10 items in React state, fine
4. Task messages in database — potentially large for complex agent runs

### Fix:
- Set maximum cap on in-memory stores (e.g., max 1000 entries)
- Switch to sliding window counter for rate limiting (lower memory)
- Make Redis mandatory for production (offloads memory)

---

## 5. Redis — ⚠️ 5/10

### Current design:
- Single Redis instance (no cluster, no sentinel)
- `str(now)` as sorted set member in rate limiter
- `KEYS *` in `rate_limit_reset()` — blocks Redis on large key spaces
- No pipeline for review store updates (read-modify-write is non-atomic)
- REVIEW_TTL = 3600s — reasonable but no cleanup of stale keys in Redis

### Rate limiter ZSET memory analysis:
Each rate limit check adds one ZSET entry for the IP. With 10 req/hour/IP and 1000 IPs, that's 10,000 entries. Each entry has the member string `str(now)` (~20 bytes) plus score (~8 bytes) plus overhead. Total: ~500KB — manageable. But at 10,000 req/hour from 1000 IPs: 10M entries → 500MB. ZREMRANGEBYSCORE removes old entries during the check, so steady-state is bounded by `limit * active_IPs`. Acceptable for now.

### Fix:
- Use `ZADD ... CH` with integer timestamp members (second precision, int is 8 bytes vs 20 for string)
- Replace `KEYS *` with a dedicated key pattern or maintain key list
- Add Redis connection retry with backoff in `init_redis()`
- Use Redis streams for review queue instead of fire-and-forget

---

## 6. Scalability Scorecard

| Dimension | Score | Limiting Factor |
|-----------|-------|-----------------|
| Multi-worker | 3/10 | In-memory state per process |
| Concurrency | 4/10 | No backpressure, unlimited create_task |
| Database | 5/10 | N+1 queries, no pagination, no replicas |
| Memory | 4/10 | Unbounded in-memory stores |
| Redis | 5/10 | Non-atomic updates, single instance |
| Queue | 2/10 | No work queue, fire-and-forget only |
| **Overall** | **4/10** | |

---

## 7. 1000 Concurrent Users Scenario

| Component | Expected Behavior | Verdict |
|-----------|------------------|---------|
| API Server | 1000 POST/s → uvicorn single worker handles ~100 req/s → queue grows → timeout | ❌ |
| Database | 1000 list_teams → 1001 queries each → 1M+ queries → connection pool exhausted | ❌ |
| Redis | Rate limiter handles ~1000 ZADD/s → fine | ✅ |
| Ollama | 1000 concurrent model calls → GPU OOM or queue timeout | ❌ |
| Memory | 1000 pending reviews → ~500MB | ⚠️ |
| Review Pipeline | No queue → 1000 concurrent create_task → event loop overload | ❌ |

**Verdict**: The system in its current form handles ~10-20 concurrent users with degraded performance. For 1000 users, significant architectural changes are needed.

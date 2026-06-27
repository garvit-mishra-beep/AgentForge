# Incident Runbook — AgentForge

**Last Updated:** June 2026

---

## Runbook 1: Agent Stuck in LangGraph Loop

### Detection
- Task runs longer than expected (e.g., >30 minutes for a task that should take 5 minutes)
- `task_steps` count for the task exceeds `MAX_STEPS` threshold (20)
- LangSmith trace shows the same node executing repeatedly

### Immediate Mitigation (< 5 min)
```bash
# 1. Kill the stuck task via admin API
curl -X POST https://api.agentforge.dev/api/v1/admin/tasks/{task_id}/cancel \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 2. Verify task is cancelled
curl https://api.agentforge.dev/api/v1/tasks/{task_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: status = "cancelled"

# 3. Notify the human who created the task via WebSocket
```

### Root Cause Investigation
1. Check LangSmith trace for the stuck task — identify which node loops
2. Check the conditional edge routing function — is it returning the correct value?
3. Check if the agent output includes a field the router depends on
4. Common causes:
   - Router function always returns the same value (bug in conditional logic)
   - Agent output missing a field the router checks
   - AI provider returning non-standard output that doesn't match expected schema

### Resolution
- Hotfix: Set `MAX_STEPS=20` in config (already done)
- Permanent fix: Fix the conditional edge logic in `graph.py`
- Add tests for the router function with edge case inputs

### Post-Incident Checklist
- [ ] Confirm fix added for the specific loop pattern
- [ ] Verify `MAX_STEPS` enforcement works
- [ ] Add regression test for loop detection
- [ ] Update runbook if new loop pattern discovered

---

## Runbook 2: WebSocket Connection Storm

### Detection
- `agentforge_ws_connections_active` spikes > 200 (baseline: 10-50)
- Redis `pub/sub` subscriber count spikes
- API server CPU/memory increases sharply
- Users report "connection lost" errors

### Immediate Mitigation (< 5 min)
```bash
# 1. Apply connection rate limit
curl -X POST https://api.agentforge.dev/api/v1/admin/config \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ws_max_connections_per_task": 3}'

# 2. Check if it's a specific task or user
grep "ws_connect" /var/log/agentforge/api.log | awk '{print $NF}' | sort | uniq -c | sort -rn

# 3. If a single task, cancel it
curl -X POST https://api.agentforge.dev/api/v1/admin/tasks/{task_id}/cancel \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 4. If a single user, temporarily suspend API access
curl -X POST https://api.agentforge.dev/api/v1/admin/users/{user_id}/suspend \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Root Cause Investigation
1. Check if a user or script is opening many WebSocket connections
2. Check if frontend auto-reconnect is creating duplicate connections
3. Check if there's a network-level issue (DDoS, misconfigured proxy)
4. Review WebSocket client code for connection leak

### Resolution
- Implement WebSocket rate limiting (already in backlog)
- Fix frontend auto-reconnect to close old connection before opening new one
- Add backpressure: reject new connections if server is at capacity

---

## Runbook 3: PostgreSQL Connection Pool Exhaustion

### Detection
- `asyncpg.exceptions._base.InterfaceError: pool is closed` in logs
- `agentforge_db_pool_size == max_pool` in Prometheus
- API endpoints return 503 errors
- Grafana dashboard shows pool at 100% utilization

### Immediate Mitigation (< 5 min)
```bash
# 1. Increase pool size temporarily
# In Railway dashboard:
# Set DATABASE_POOL_MAX = 50 (from default 10)

# 2. Restart the API service to apply new pool size
# Railway dashboard → Deploy → Redeploy

# 3. Verify recovery
curl https://api.agentforge.dev/api/v1/health
# Should return 200 OK
```

### Root Cause Investigation
1. Check for leaking connections: are there async operations that don't release connections?
2. Check if a specific endpoint creates many concurrent DB connections
3. Check if there's a deadlock causing connections to hang
4. Review `asyncpg.connect()` usage — ensure `async with` or `await conn.close()` is always used

### Resolution
- Fix connection leaks by auditing all `asyncpg` usage
- Add connection timeout: `pool.acquire(timeout=30)` to prevent indefinite waits
- Implement circuit breaker: when pool hits 80%, slow down new requests

---

## Runbook 4: Redis Out of Memory

### Detection
- `Redis Error: OOM command not allowed when used memory > 'maxmemory'` in logs
- `INFO memory` shows `used_memory > maxmemory`
- Redis eviction keys counter spikes (`evicted_keys`)

### Immediate Mitigation (< 5 min)
```bash
# 1. Check Redis memory usage
redis-cli INFO memory | findstr "used_memory_human maxmemory_human"

# 2. Set eviction policy to allkeys-lru (if not already)
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 3. Flush expired keys
redis-cli MEMORY PURGE

# 4. Increase maxmemory (if Railway managed, upgrade plan)
```

### Root Cause Investigation
1. Check which keys consume the most memory: `redis-cli --bigkeys`
2. Check for keys without TTL: `redis-cli INFO keyspace`
3. Common causes:
   - JWT cache keys missing TTL (known bug P1-005)
   - Agent event pub/sub channels accumulating stale subscribers
   - Rate limit counters not expiring

### Resolution
- Set TTL on all cache keys (JWT: 3600s, rate limit: 60s)
- Add memory limit alerts in Grafana
- Implement periodic `MEMORY PURGE` job

---

## Runbook 5: AI Provider API Key Rate Limited

### Detection
- HTTP 429 responses from AI provider API
- `agentforge_agent_errors_total{error_type="rate_limit"}` increases
- Agents fail with "Rate limit exceeded" messages

### Immediate Mitigation (< 5 min)
```bash
# 1. Switch to fallback model
# In the model_registry.py, the fallback chain is automatic:
# GPT-4o → GPT-4o-mini
# Claude Sonnet → Claude Haiku
# If all fallbacks also rate limited:

# 2. Pause task queue
curl -X POST https://api.agentforge.dev/api/v1/admin/queue/pause \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Notify users of degraded service
```

### Root Cause Investigation
1. Check current usage against model's rate limit (see MODEL_REGISTRY.md)
2. Check if there's a burst of tasks using the same model
3. Check if the API key is shared across environments (dev + staging + prod)

### Resolution
- Upgrade API key tier for higher rate limits (paid plans)
- Implement request queuing with rate limit awareness
- Rotate keys if compromised or shared
- Distribute load across multiple API keys

---

## Runbook 6: Vercel Deploy Failure

### Detection
- GitHub Actions workflow shows ❌ for deploy-frontend job
- Vercel dashboard shows "Failed" deployment
- Users report they don't see the latest changes

### Immediate Mitigation (< 5 min)
1. Go to Vercel dashboard → Deployments
2. Find the last successful deployment
3. Click "..." → "Promote to Production"
4. Verify: `https://agentforge.app` loads correctly

### Root Cause Investigation
1. Check GitHub Actions logs for build error details
2. Common causes:
   - TypeScript compilation error in new code
   - Missing environment variable in Vercel project settings
   - Dependency installation failure (network issue, package not found)
   - Monorepo dependency — changes in `packages/` not published

### Resolution
- Fix the build error and push a new commit
- If env var issue: add to Vercel dashboard and re-run deployment
- Add `turbo.json` caching fix if cache invalidation issue

---

## Incident Response Contacts

| Role | Contact | Escalation Path |
|------|---------|----------------|
| On-call engineer | #on-call Slack channel | Immediate |
| Backend team lead | @backend-lead Slack | If backend-related |
| DevOps | #devops Slack | If infra-related (DB, Redis, deploy) |
| CTO | @cto Slack | If customer-impacting > 30 min |

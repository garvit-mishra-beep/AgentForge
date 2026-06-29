# Pillar 3: Integration Audit Report

This report documents the findings from the integration audit between the Next.js frontend (`apps/web/`) and the FastAPI backend (`apps/api/`).

---

## 3.1 REST Contract Mismatches

| Frontend Call | Backend Route & File | Schema Match | Severity | Finding & Impact | Fix |
|---|---|---|---|---|---|
| `createTask` in [api.ts:161](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L161) | `POST /api/v1/tasks` in [tasks.py:46](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/tasks.py#L46) | ❌ **MISMATCH** | P1 | Frontend constructs a body variable that ignores `project_id` even if passed. Tasks created from the frontend are never associated with a project in the database, losing context. | Include `project_id: data.project_id` in the request body dictionary inside `createTask`. |
| `uploadFile` / `uploadZip` in [api.ts:216, 243](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L216) | `POST /projects/{id}/upload` in [projects.py:256](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/projects.py#L256) | ⚠️ **PARTIAL** | P2 | Upload functions bypass the unified `request` helper. They do not send `X-Request-ID` headers or support automatic token refresh on 401 errors. | Refactor upload methods to utilize the core `request` helper or support standard 401 retry interceptors. |
| `listTasks` in [api.ts:149](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L149) | `GET /api/v1/tasks` in [tasks.py:96](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/tasks.py#L96) | ❌ **MISMATCH** | P2 | Frontend attempts to send `project_id` and `team_id` as query parameters, but the backend router completely ignores them and only accepts `limit` and `offset`. | Update the backend `list_tasks` route parameters to accept and filter by `project_id` and `team_id`. |
| `listExecutions` in [api.ts:179](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L179) | `GET /api/v1/executions` in [executions.py:72](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/executions.py#L72) | ❌ **MISMATCH** | P2 | Frontend sends `project_id` query filter, but the backend endpoint only lists all executions for the user with no project-level filtering. | Add `project_id` filter argument to the backend `list_executions` endpoint. |

---

## 3.2 WebSocket Contract Verification

### Connection URL & Handler Mismatch
- **Frontend Location**: [apps/web/app/tasks/\[id\]/page.tsx:188](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/%5Bid%5D/page.tsx#L188)
- **Backend Location**: None (Missing endpoint)
- **Severity**: P0 (Critical)
- **Finding**: The frontend instantiates a connection to `ws://localhost:8000/api/v1/ws/tasks/{id}`, but the backend registers no such router or WebSocket event handlers.
- **Impact**: Real-time message streaming is completely broken in staging/production, forcing the frontend to fall back to performance-heavy API polling.
- **Fix**: Create a WebSocket handler route `/api/v1/ws/tasks/{task_id}` in a new file `apps/api/app/ws/task_stream.py`.

---

### Missing WebSocket Auth Negotiator
- **Frontend Location**: [apps/web/lib/ws-client.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/ws-client.ts#L41)
- **Backend Location**: None
- **Severity**: P1 (High)
- **Finding**: The WebSocket client does not authenticate connection requests.
- **Impact**: The backend has no token to authorize the websocket, blocking any authenticated task message stream.
- **Fix**: Pass the Bearer JWT token in the query params of the WS connection URL and parse/verify it on the backend on connection handshake.

---

## 3.3 Authentication Integration

### Frontend-Backend Token Sync Race Conditions
- **Frontend Location**: [apps/web/lib/api.ts:15-25](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L15)
- **Backend Location**: [apps/api/app/routes/auth.py:124-149](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/auth.py#L124)
- **Severity**: P2 (Medium)
- **Finding**: Frontend implements a client-side `refreshLock` to prevent duplicate parallel requests. However, the backend lacks database locks during token rotation.
- **Impact**: If two tabs or separate devices refresh at the exact same moment, the backend can hit race conditions, rotating the token twice and invalidating the user's session due to token reuse flags.
- **Fix**: Implement row-level lock on token check-and-revoke queries in PostgreSQL.

---

## 3.4 GitHub App Integration

### Missing Installation Token Caching
- **File**: [apps/api/app/integrations/github.py](file:///c:/Users/garvi/AgentForge/apps/api/app/integrations/github.py#L89-L100)
- **Severity**: P1 (High)
- **Finding**: The GitHub App client mints a fresh installation token by making an HTTP post to GitHub's REST endpoints on every event hook invocation.
- **Impact**: High volumes of PR webhook events will trigger rate-limit blocks from the GitHub API due to repeated token generations.
- **Fix**: Cache the installation access token in Redis with a TTL of 50 minutes (since tokens expire in 1 hour).

---

## 3.5 BYOK Integration

### Decryption Ephemeral Key Failure
- **File**: [apps/api/core/encryption.py](file:///c:/Users/garvi/AgentForge/apps/api/core/encryption.py#L19-L24)
- **Severity**: P1 (High)
- **Finding**: If the server falls back to an ephemeral key, keys stored in the database fail decryption after server restarts.
- **Impact**: Model routing fails once the database contains keys encrypted with a lost key.
- **Fix**: Block server start if `AGENTFORGE_ENCRYPTION_KEY` is not present when auth is enabled.

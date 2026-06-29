# WebSocket Event Map

## Status: ❌ No WebSocket Support

After auditing all backend route files and the full directory tree under `apps/api/`, **there is no WebSocket directory or WebSocket endpoint**.

### Evidence
- `apps/api/app/routes/` — contains 15 files, none implement WebSocket
- `apps/api/app/ws/` — **directory does not exist** (confirmed by glob search)
- `apps/api/app/main.py` — includes 13 HTTP routers; no WebSocket handler registered
- No `websocket` import exists in any route file

### Impact
- Frontend `lib/ws-client.ts` and `types/ws.ts` are dead code
- `/tasks/[id]` and `/executions/[id]` pages **must poll** via `GET /api/v1/tasks/{id}/messages` and `GET /api/v1/executions/detail/{exec_id}`
- Real-time streaming of agent messages is not possible
- No push-based status updates for task execution progress

### Pre-Defined Event Types (frontend-only, unused)
These types exist in `types/ws.ts` but have no backend counterpart:

| Event | Direction | Purpose |
|-------|-----------|---------|
| agent_message | server→client | Streaming agent output |
| task_status_update | server→client | Status transitions |
| execution_log | server→client | Log output |
| team_update | server→client | Team changes |
| artifact_update | server→client | Build artifacts |

### Fallback Strategy
- Poll `GET /api/v1/tasks/{task_id}/messages` every 500-600ms for task progress
- Poll `GET /api/v1/executions/detail/{exec_id}` for execution status
- Use setTimeout-based polling with exponential backoff on errors

### Priority: P0 (Critical)
Logged in `BACKEND_GAPS.md` — blocks real-time streaming UI.

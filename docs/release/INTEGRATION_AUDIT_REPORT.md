# Integration Audit Report

**Product:** AgentForge Platform  
**Auditor:** Senior Engineering Auditor  
**Scope:** Frontend-Backend Contracts (REST, WebSockets, GitHub Webhooks)  
**Date:** June 29, 2026  

---

## 1. Summary of Findings

| Severity | Count | Status |
|:---|:---:|:---|
| **P0 (Critical)** | 0 | ✅ Clean |
| **P1 (High)** | 2 | ❌ Action Required |
| **P2 (Medium)** | 0 | ✅ Clean |
| **P3 (Low)** | 0 | ✅ Clean |

---

## 2. Findings Detail

### createTask strips project_id Parameter
- **Location Pair**:
  - **Frontend call**: `apps/web/lib/api.ts` · Lines 161–164
  - **Backend route**: `apps/api/app/routes/tasks.py` · Line 46
  - **Schema match**: ⚠️ MISMATCH
- **Severity**: P1 (High)
- **Finding**: The frontend `createTask` function accepts `project_id` but excludes it when constructing the `body` dictionary payload.
- **Impact**: Any task created via the frontend dashboard ignores its project context, resulting in orphaned tasks in the database with no project link.
- **Proof**:
  ```typescript
  export function createTask(data: { team_id: string; title: string; description: string; project_id?: string }): Promise<Task> {
    const body: Record<string, string> = { team_id: data.team_id, title: data.title, description: data.description };
    return api.post("/tasks", body); // project_id is missing from body
  }
  ```
- **Fix**: Update the `body` creation to include `project_id` when present:
  ```typescript
  const body: Record<string, any> = {
    team_id: data.team_id,
    title: data.title,
    description: data.description,
    ...(data.project_id ? { project_id: data.project_id } : {})
  };
  ```

---

### Non-Existent WebSocket API on Backend
- **Location Pair**:
  - **Frontend client**: `apps/web/lib/ws-client.ts` · Lines 22–122
  - **Backend gateway**: `apps/api/app/main.py`
  - **Schema match**: ❌ MISSING IMPLEMENTATION
- **Severity**: P1 (High)
- **Finding**: The web client includes a wrapper for WebSockets (`WSClient`) to stream execution updates, but the backend FastAPI application defines no WebSocket handlers (`@app.websocket`) and mounts no WebSocket routers.
- **Impact**: Real-time task step updates are completely non-functional. Clicking a task in the UI connects to a non-existent port endpoint, failing to load live updates.
- **Proof**: A search for `websocket` across all Python source files in `apps/api/app/` returns zero hits.
- **Fix**: Mount a WebSocket handler in `apps/api/app/main.py` or separate routes module that subscribes to Redis Pub/Sub events for task IDs and streams updates back to the client.

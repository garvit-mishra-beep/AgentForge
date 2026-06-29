# Integration Remediation Plan

This document outlines the remediation plan for findings identified in the integration audit.

---

## 1. Remediation Schedule

| Task ID | Severity | Effort | Component | Description | Dependency |
|:---|:---:|:---:|:---|:---|:---|
| **INT-01** | **P1** | S | apps/web/lib/api.ts | Update `createTask` in frontend client to serialize and pass `project_id`. | None |
| **INT-02** | **P1** | L | apps/api/app/main.py | Implement the `/api/v1/tasks/ws/{task_id}` WebSocket router in FastAPI backend to broadcast graph states. | None |

---

## 2. Details of High Priority Remediation (P1)

### INT-01: createTask project_id serialization
- **Action**: Modify the helper in `apps/web/lib/api.ts`:
  ```typescript
  export function createTask(data: { team_id: string; title: string; description: string; project_id?: string }): Promise<Task> {
    const body: Record<string, any> = {
      team_id: data.team_id,
      title: data.title,
      description: data.description,
    };
    if (data.project_id) {
      body.project_id = data.project_id;
    }
    return api.post("/tasks", body);
  }
  ```

### INT-02: Backend WebSocket setup
- **Action**: Add a WebSocket endpoint in backend routes:
  ```python
  from fastapi import WebSocket, WebSocketDisconnect
  
  @router.websocket("/tasks/ws/{task_id}")
  async def websocket_task_stream(websocket: WebSocket, task_id: str):
      await websocket.accept()
      # Subscribe to Redis pub/sub channel for task_id
      pubsub = redis_client.pubsub()
      await pubsub.subscribe(f"task:{task_id}")
      try:
          while True:
              message = await pubsub.get_message(ignore_subscribe_messages=True)
              if message:
                  await websocket.send_text(message["data"])
              await asyncio.sleep(0.1)
      except WebSocketDisconnect:
          await pubsub.unsubscribe(f"task:{task_id}")
  ```

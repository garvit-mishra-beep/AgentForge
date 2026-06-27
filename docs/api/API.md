# API Reference — AgentForge

**Last Updated:** June 2026

---

## Base URL

- **Local:** `http://localhost:8000`
- **Production:** `https://api.agentforge.dev`

## Authentication

All endpoints (except `/health` and `/auth/verify`) require a Clerk JWT token in the `Authorization` header:

```
Authorization: Bearer <clerk_jwt_token>
```

The JWT is obtained by signing in via Clerk's frontend SDK. The FastAPI middleware validates the token's signature, expiry, and extracts the `user_id`.

---

## REST API Endpoints

### Health

```
GET /api/v1/health
```

No auth required. Returns service status.

**Response:**
```json
{ "status": "ok", "version": "0.3.0" }
```

---

### Auth

#### Verify Clerk JWT

```
POST /api/v1/auth/verify
```

**Auth:** None (used internally by middleware)

**Request Body:**
```json
{ "token": "clerk_jwt_token_string" }
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "https://img.clerk.com/xxx"
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "your_clerk_jwt_token"}'
```

---

### Projects

#### List Projects

```
GET /api/v1/projects
```

**Auth:** Required

**Query Parameters:** None

**Response:**
```json
{
  "projects": [
    {
      "id": "proj_abc123",
      "name": "My Project",
      "description": "A sample project",
      "owner_id": "user_abc123",
      "created_at": "2026-06-01T00:00:00Z",
      "updated_at": "2026-06-25T00:00:00Z"
    }
  ]
}
```

**curl:**
```bash
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>"
```

#### Create Project

```
POST /api/v1/projects
```

**Auth:** Required

**Request Body:**
```json
{
  "name": "My Project",
  "description": "Optional description"
}
```

**Response:** `201 Created`
```json
{
  "id": "proj_abc123",
  "name": "My Project",
  "description": "Optional description",
  "owner_id": "user_abc123",
  "created_at": "2026-06-25T00:00:00Z"
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project"}'
```

#### Get Project

```
GET /api/v1/projects/{project_id}
```

**Auth:** Required (must be member)

**Response:**
```json
{
  "id": "proj_abc123",
  "name": "My Project",
  "description": "A sample project",
  "owner_id": "user_abc123",
  "teams": [],
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-06-25T00:00:00Z"
}
```

#### Update Project

```
PATCH /api/v1/projects/{project_id}
```

**Auth:** Required (must be owner or admin)

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response:** `200 OK` with updated project object.

#### Delete Project

```
DELETE /api/v1/projects/{project_id}
```

**Auth:** Required (must be owner)

**Response:** `204 No Content`

---

### Teams

#### List Teams (for a project)

```
GET /api/v1/projects/{project_id}/teams
```

**Auth:** Required (must be project member)

**Response:**
```json
{
  "teams": [
    {
      "id": "team_abc123",
      "project_id": "proj_abc123",
      "name": "My AI Team",
      "created_at": "2026-06-01T00:00:00Z"
    }
  ]
}
```

#### Create Team

```
POST /api/v1/projects/{project_id}/teams
```

**Auth:** Required (must be project admin)

**Request Body:**
```json
{
  "name": "My AI Team"
}
```

**Response:** `201 Created`

---

### Agents (within a Team)

#### List Agents

```
GET /api/v1/teams/{team_id}/agents
```

**Auth:** Required

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_abc123",
      "team_id": "team_abc123",
      "role": "team_lead",
      "model": "gemini-1.5-pro",
      "is_active": true,
      "created_at": "2026-06-01T00:00:00Z"
    }
  ]
}
```

#### Add Agent to Team

```
POST /api/v1/teams/{team_id}/agents
```

**Auth:** Required

**Request Body:**
```json
{
  "role": "backend",
  "model": "claude-sonnet-4-6"
}
```

**Response:** `201 Created`

**Validation:** The `role` must be one of: `team_lead`, `backend`, `frontend`, `qa`, `security`, `devops`. The `model` must be a valid model ID from the [Model Registry](MODEL_REGISTRY.md). Each role can only appear once per team.

#### Remove Agent from Team

```
DELETE /api/v1/teams/{team_id}/agents/{agent_id}
```

**Auth:** Required

**Response:** `204 No Content`

---

### Tasks

#### Create Task

```
POST /api/v1/tasks
```

**Auth:** Required

**Request Body:**
```json
{
  "project_id": "proj_abc123",
  "team_id": "team_abc123",
  "title": "Build JWT Authentication",
  "description": "Implement JWT-based authentication with login and refresh endpoints."
}
```

**Response:** `201 Created`
```json
{
  "id": "task_abc123",
  "project_id": "proj_abc123",
  "team_id": "team_abc123",
  "title": "Build JWT Authentication",
  "description": "Implement JWT-based authentication with login and refresh endpoints.",
  "status": "pending",
  "created_by": "user_abc123",
  "created_at": "2026-06-25T12:00:00Z"
}
```

After creation, the task is picked up by the orchestrator and execution begins.

#### Get Task

```
GET /api/v1/tasks/{task_id}
```

**Auth:** Required

**Response:**
```json
{
  "id": "task_abc123",
  "project_id": "proj_abc123",
  "team_id": "team_abc123",
  "title": "Build JWT Authentication",
  "description": "Implement JWT-based authentication with login and refresh endpoints.",
  "status": "running",
  "steps": [
    {
      "id": "step_001",
      "step_order": 1,
      "role": "team_lead",
      "status": "completed",
      "model": "gemini-1.5-pro",
      "tokens_in": 4500,
      "tokens_out": 1200,
      "cost": 0.007125,
      "started_at": "2026-06-25T12:00:05Z",
      "completed_at": "2026-06-25T12:00:15Z"
    },
    {
      "id": "step_002",
      "step_order": 2,
      "role": "backend",
      "status": "running",
      "model": "claude-sonnet-4-6",
      "tokens_in": 0,
      "tokens_out": 0,
      "cost": 0.0,
      "started_at": "2026-06-25T12:00:16Z",
      "completed_at": null
    }
  ],
  "total_tokens": 5700,
  "total_cost": 0.007125,
  "created_by": "user_abc123",
  "created_at": "2026-06-25T12:00:00Z",
  "updated_at": "2026-06-25T12:00:16Z",
  "completed_at": null
}
```

#### Get Task Steps

```
GET /api/v1/tasks/{task_id}/steps
```

**Auth:** Required

**Response:** Array of task step objects (same schema as inline in Get Task).

#### Get Task Output (Files)

```
GET /api/v1/tasks/{task_id}/output
```

**Auth:** Required

**Response:**
```json
{
  "outputs": [
    {
      "id": "out_abc123",
      "step_id": "step_002",
      "agent_id": "agent_backend_001",
      "file_path": "app/services/auth.py",
      "file_content": "from datetime import timedelta\n...",
      "language": "python",
      "created_at": "2026-06-25T12:00:30Z"
    }
  ]
}
```

#### Request Task Revision

```
POST /api/v1/tasks/{task_id}/revise
```

**Auth:** Required

**Request Body:**
```json
{
  "feedback": "The JWT secret should be read from env, not hardcoded."
}
```

**Response:** `202 Accepted`

The task will be restarted from step 2 (Backend Engineer) with the feedback injected as review context.

---

### History

#### Task History

```
GET /api/v1/history
```

**Auth:** Required

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Filter by project |
| `status` | string | Filter by status (`completed`, `failed`, `cancelled`) |
| `date_from` | ISO 8601 | Start date filter |
| `date_to` | ISO 8601 | End date filter |
| `limit` | integer | Max results (default: 50, max: 100) |
| `offset` | integer | Pagination offset |

**Response:**
```json
{
  "tasks": [
    {
      "id": "task_abc123",
      "title": "Build JWT Authentication",
      "status": "completed",
      "total_tokens": 18000,
      "total_cost": 0.054,
      "created_at": "2026-06-25T12:00:00Z",
      "completed_at": "2026-06-25T12:04:32Z"
    }
  ],
  "total": 42
}
```

---

## WebSocket API

### Connection

```
ws://localhost:8000/ws/tasks/{task_id}
```

**Auth:** JWT token sent as first message after connection:
```json
{
  "type": "auth",
  "token": "<clerk_jwt_token>"
}
```

### Event Types

#### Server → Client Events

| Event Type | Description | Payload |
|------------|-------------|---------|
| `task_created` | Task has been created and queued | `{ task_id, title }` |
| `task_started` | Orchestrator has begun execution | `{ task_id, team_config }` |
| `agent_started` | An agent node has started | `{ agent_id, role, model }` |
| `agent_message` | Streaming token output from agent | `{ agent_id, role, content_chunk, is_final }` |
| `agent_complete` | An agent node has finished | `{ agent_id, role, tokens_in, tokens_out, cost, confidence }` |
| `handoff` | Agent A passed output to Agent B | `{ from_role, to_role }` |
| `human_interrupt` | Waiting for human approval | `{ step, message, options: ["approve", "reject", "revise"] }` |
| `task_complete` | Full task execution finished | `{ task_id, status, total_tokens, total_cost, summary }` |
| `task_error` | Task failed with error | `{ task_id, error_type, error_message }` |

#### Client → Server Events

| Event Type | Description | Payload |
|------------|-------------|---------|
| `auth` | Authentication (first message) | `{ token }` |
| `human_approved` | Human approves the deliverable | `{ task_id }` |
| `human_rejected` | Human rejects with feedback | `{ task_id, feedback }` |

### Event Envelope Format

All events use this structure:

```json
{
  "type": "agent_message",
  "task_id": "task_abc123",
  "agent_id": "agent_backend_001",
  "role": "backend",
  "model": "claude-sonnet-4-6",
  "timestamp": "2026-06-25T12:00:20Z",
  "payload": {
    "content_chunk": "def create_access_token(...)",
    "is_final": false
  }
}
```

### WebSocket Client Example

```typescript
// apps/web/lib/ws-client.ts
const ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`);

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "auth", token: clerkToken }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch (message.type) {
    case "agent_message":
      // Append content_chunk to output panel
      break;
    case "agent_complete":
      // Show agent summary
      break;
    case "human_interrupt":
      // Show approval dialog
      break;
    case "task_complete":
      // Show final deliverable
      break;
  }
};

ws.onclose = () => {
  // Auto-reconnect with exponential backoff
};
```

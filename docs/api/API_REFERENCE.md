# API Reference Specification — AgentForge

The AgentForge Backend Gateway API serves REST endpoints for user accounts, credentials, and tasks, alongside WebSocket routes for real-time agent output streaming.

---

## 1. Authentication & Tenant Scope

All requests to protected endpoints must attach a valid JWT access token as a bearer authentication header:
```text
Authorization: Bearer <access_jwt_token>
```
Endpoints automatically filter query results and restrict modifications based on the decoded token's user identity (`user_id`).

---

## 2. API Endpoints

### 🔑 Authentication Module

#### `POST /api/v1/auth/register`
* **Purpose:** Create a new user profile.
* **Request Schema:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword",
    "name": "Developer Name"
  }
  ```
* **Response Schema (201 Created):**
  ```json
  {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "email": "user@example.com"
  }
  ```

#### `POST /api/v1/auth/login`
* **Purpose:** Authenticate and retrieve JWT tokens.
* **Request Schema:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
* **Response Schema (200 OK):**
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer"
  }
  ```

#### `POST /api/v1/auth/refresh`
* **Purpose:** Refresh an expired access token using a refresh token.
* **Request Schema:**
  ```json
  {
    "refresh_token": "eyJhbG..."
  }
  ```
* **Response Schema (200 OK):**
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer"
  }
  ```

---

### 📝 Code Review Module

#### `POST /api/v1/review`
* **Purpose:** Submit code for analysis by the builder/reviewer pipeline.
* **Request Schema:**
  ```json
  {
    "code": "def parse_auth(header): ...",
    "language": "python"
  }
  ```
* **Response Schema (200 OK):**
  ```json
  {
    "review_id": "a85c5f66-583f-4d9e-bdba-a4337715eccb",
    "status": "queued"
  }
  ```

#### `GET /api/v1/review/{review_id}`
* **Purpose:** Retrieve the status or completed analysis report for a specific review request.
* **Response Schema (200 OK):**
  ```json
  {
    "review_id": "a85c5f66-583f-4d9e-bdba-a4337715eccb",
    "status": "completed",
    "baseline_issues": [],
    "builder_output": "...",
    "review_issues": [
      {
        "category": "security",
        "description": "Hardcoded credential token detected in module.",
        "line": 42
      }
    ],
    "summary": "Code logic verified. Correct security vulnerability identified on line 42.",
    "model_used": "phi4-mini",
    "created_at": "2026-06-27T08:30:00Z",
    "completed_at": "2026-06-27T08:31:00Z"
  }
  ```

---

### 📡 WebSocket Event Stream

#### `WS /api/v1/executions/{execution_id}/stream`
Streams incremental event states, token outputs, and validation metrics during agent execution.

##### Event Type Formats
* **`agent_started`:** Emitted when a specific node begins processing.
  ```json
  {
    "event": "agent_started",
    "agent": "builder",
    "timestamp": "2026-06-27T08:30:15Z"
  }
  ```
* **`token_chunk`:** Incremental token output.
  ```json
  {
    "event": "token_chunk",
    "agent": "builder",
    "text": "def "
  }
  ```
* **`agent_completed`:** Emitted when a specific node finishes execution.
  ```json
  {
    "event": "agent_completed",
    "agent": "builder",
    "output_summary": "Generated JWT auth class middleware."
  }
  ```

# Pillar 3: Integration Remediation Plan

This remediation plan lists the required integration fixes in order of priority (highest severity first).

---

## Remediation Tasks

### 1. Implement Task project_id Attachment in Frontend Client
- **Finding ID**: `createTask` Mismatch
- **Severity**: P1 (High)
- **File**: [apps/web/lib/api.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L161-L164)
- **Remediation**:
  Modify the request body in `createTask` to forward `project_id` when defined:
  ```typescript
  export function createTask(data: { team_id: string; title: string; description: string; project_id?: string }): Promise<Task> {
    const body: Record<string, string> = {
      team_id: data.team_id,
      title: data.title,
      description: data.description,
      ...(data.project_id ? { project_id: data.project_id } : {}),
    };
    return api.post("/tasks", body);
  }
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 2. Add Caching for GitHub Installation Tokens
- **Finding ID**: Missing Installation Token Caching
- **Severity**: P1 (High)
- **File**: [apps/api/app/integrations/github.py](file:///c:/Users/garvi/AgentForge/apps/api/app/integrations/github.py#L89)
- **Remediation**:
  Store the generated installation token in Redis (using key name format `gh_install_token:{installation_id}`) with an expiration offset of 50 minutes. Check the cache before calling `/access_tokens`.
- **Estimated Effort**: M (Medium)
- **Dependencies**: Redis layer initialization.

---

### 3. Support Token Refresh in File Upload Hooks
- **Finding ID**: `uploadFile` / `uploadZip` Interceptor Bypass
- **Severity**: P2 (Medium)
- **File**: [apps/web/lib/api.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L216-L267)
- **Remediation**:
  Rewrite file uploads to use a custom fetch wrapper or attach the refresh retry block to FormData requests, aligning them with standard JSON client behaviors.
- **Estimated Effort**: M (Medium)
- **Dependencies**: None.

---

### 4. Enable Server-Side Query Filters for listTasks
- **Finding ID**: `listTasks` Query Parameter Mismatch
- **Severity**: P2 (Medium)
- **File**: [apps/api/app/routes/tasks.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/tasks.py#L96-L102)
- **Remediation**:
  Add `project_id: str | None = Query(None)` and `team_id: str | None = Query(None)` parameters in the backend `list_tasks` route, and dynamically build the SQL WHERE clauses:
  ```python
  query = "SELECT ... FROM tasks WHERE created_by = $1"
  params = [user_id]
  # Build filters dynamically
  ```
- **Estimated Effort**: M (Medium)
- **Dependencies**: None.

---

### 5. Enable Server-Side Query Filters for listExecutions
- **Finding ID**: `listExecutions` Query Parameter Mismatch
- **Severity**: P2 (Medium)
- **File**: [apps/api/app/routes/executions.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/executions.py#L72-L78)
- **Remediation**:
  Add `project_id: str | None = Query(None)` support to backend list execution router and filter the query scope accordingly.
- **Estimated Effort**: M (Medium)
- **Dependencies**: None.

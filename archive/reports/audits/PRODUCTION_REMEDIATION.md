# Pillar 4: Production Remediation Plan

This remediation plan lists the required production readiness fixes in order of priority (highest severity first).

---

## Remediation Tasks

### 1. Fix Path Traversal Guard in File Uploads
- **Finding ID**: Security: Folder Prefix Hijacking
- **Severity**: P0 (Critical)
- **File**: [apps/api/app/routes/projects.py](file:///c:/Users/garvi/AgentForge/apps/api/app/routes/projects.py#L46-L52)
- **Remediation**:
  Replace prefix checking with structured subpath validation via `Path.relative_to`:
  ```python
  def _validate_filepath(storage_path: Path) -> None:
      resolved = storage_path.resolve()
      upload_resolved = UPLOAD_DIR.resolve()
      try:
          resolved.relative_to(upload_resolved)
      except ValueError:
          raise HTTPException(status_code=400, detail="Invalid file path")
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None. Apply immediately.

---

### 2. Upgrade Outdated Python Packages
- **Finding ID**: Outdated Vulnerable Python Dependencies
- **Severity**: P1 (High)
- **File**: [apps/api/requirements.txt](file:///c:/Users/garvi/AgentForge/apps/api/requirements.txt)
- **Remediation**:
  Upgrade packages in `requirements.txt` to newer versions to address high-severity CVEs:
  - Update `cryptography` from `41.0.3` to `43.0.0` or higher.
  - Update `fastapi` from `0.104.1` to `0.109.0` or higher.
- **Estimated Effort**: S (Small)
- **Dependencies**: Requires running test suites afterward to check for breaking changes in newer FastAPI APIs.

---

### 3. Fail Executions Correctly on Task Timeout
- **Finding ID**: Reliability: Dangling Execution Status on Timeout
- **Severity**: P2 (Medium)
- **File**: [apps/api/agents/orchestrator.py](file:///c:/Users/garvi/AgentForge/apps/api/agents/orchestrator.py#L207-L212)
- **Remediation**:
  Add database update execution step inside `TimeoutError` except block to update `executions` table status:
  ```python
  except TimeoutError:
      logger.error("Task %s timed out", task_id)
      await db.execute(
          "UPDATE tasks SET status = 'failed', error_message = 'Execution timed out', updated_at = NOW() WHERE id = $1",
          task_id,
      )
      await db.execute(
          "UPDATE executions SET status = 'failed', error_message = 'Execution timed out', completed_at = NOW() WHERE task_id = $1",
          task_id,
      )
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 4. Fetch correlation_id from Request Context in Logger
- **Finding ID**: Tracing: Correlation ID Missing in Log Formatter
- **Severity**: P2 (Medium)
- **File**: [apps/api/core/logging_config.py](file:///c:/Users/garvi/AgentForge/apps/api/core/logging_config.py#L9-L21)
- **Remediation**:
  Modify the `JSONFormatter` to dynamically fetch the correlation ID from context local storage (e.g. contextvars) when serializing message payloads.
- **Estimated Effort**: S (Small)
- **Dependencies**: Register `CorrelationFilter` to console output handlers first.

---

### 5. Validate Optional Operational Secrets on Server Boot
- **Finding ID**: Startup Config Validation Gaps
- **Severity**: P3 (Low)
- **File**: [apps/api/core/config.py](file:///c:/Users/garvi/AgentForge/apps/api/core/config.py#L95)
- **Remediation**:
  In `Settings.validate()`, append warnings or fail-fast validation checks for Redis and external integrations if the user attempts to run tasks that rely on those adapters.
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

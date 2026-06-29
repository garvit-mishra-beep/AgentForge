# Production Remediation Plan

This document outlines the remediation plan for findings identified in the production readiness audit.

---

## 1. Remediation Schedule

| Task ID | Severity | Effort | Component | Description | Dependency |
|:---|:---:|:---:|:---|:---|:---|
| **PR-01** | **P1** | M | core/providers.py | Add tenacity-based retry with exponential backoff for transient LLM provider failures. | None |
| **PR-02** | **P1** | M | core/task_tracker.py | Implement task graceful shutdown grace periods and catch CancelledError to mark tasks failed on exit. | None |

---

## 2. Details of High Priority Remediation (P1)

### PR-01: LLM call retry loop
- **Action**: Wrap the chat requests:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
  
  # We should only retry on rate limits and 5xx failures, not standard validation errors
  def is_transient_error(exception):
      if isinstance(exception, httpx.HTTPStatusError):
          return exception.response.status_code in [429, 500, 502, 503, 504]
      return True # or check connection errors
  
  # Apply retry decorator to chat implementation
  ```

### PR-02: Graceful task shutdown
- **Action**: Update `shutdown` in `TaskTracker`:
  ```python
  async def shutdown(self, timeout: float = 30.0) -> None:
      self._shutdown_event.set()
      if not self._tasks:
          return
      
      # Allow a grace period of timeout * 0.8 seconds to complete tasks
      try:
          await asyncio.wait_for(asyncio.gather(*self._tasks, return_exceptions=True), timeout=timeout * 0.8)
      except asyncio.TimeoutError:
          pass
      
      # Cancel whatever remains
      for task in list(self._tasks):
          if not task.done():
              task.cancel()
  ```
  And update `run_task` to handle `asyncio.CancelledError`:
  ```python
  except asyncio.CancelledError:
      # Write 'failed' state on shutdown cancellation
      await db.execute("UPDATE tasks SET status = 'failed', error_message = 'Task cancelled on server shutdown' WHERE id = $1", task_id)
      raise
  ```

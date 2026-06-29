# Backend Remediation Plan

This document outlines the remediation plan for findings identified in the backend audit.

---

## 1. Remediation Schedule

| Task ID | Severity | Effort | Component | Description | Dependency |
|:---|:---:|:---:|:---|:---|:---|
| **BE-01** | **P0** | S | routes/review.py | Fix missing JWT `Depends(require_user)` auth bypass on Code Review routes. | None |
| **BE-02** | **P0** | S | routes/review.py | Pass `db` session parameter to `registry.get_provider_for_user()` inside review tasks. | None |
| **BE-03** | **P0** | M | routes/projects.py | Stream file uploads in 8KB chunks to enforce size limits before buffer exhausts memory. | None |
| **BE-04** | **P1** | S | routes/projects.py | Restrict Zip extraction paths to project-specific target folders to prevent tenant escape. | None |
| **BE-05** | **P1** | S | routes/projects.py | Implement Zip Bomb file size/count limits during archive extraction. | None |
| **BE-06** | **P1** | S | core/redis.py | Append UUID / random token suffix to ZADD members in rate limiter to avoid second-based key collisions. | None |
| **BE-07** | **P1** | L | app/memory_service.py | Migrate memories to pgvector using text embeddings and cosine similarity search. | None |
| **BE-08** | **P2** | S | routes/tasks.py | Add `Query(ge=1, le=200)` pagination constraints to Tasks and Teams listing. | None |
| **BE-09** | **P2** | L | agents/graph.py | Connect conditional branching edges for evidence validation failures inside LangGraph. | None |

---

## 2. Details of High Priority Remediation (P0 / P1)

### BE-01: Auth Bypass fix in review routes
- **Action**: Change route parameter binding:
  ```python
  # before
  async def get_review(review_id: str, user_id: str | None = None)
  
  # after
  async def get_review(review_id: str, user_id: str = Depends(require_user))
  ```

### BE-02: DB session crash in review routes
- **Action**: Extract `db` session and forward it to `_process_review` task:
  ```python
  # inside submit_review
  background_tasks.add_task(_process_review, review_id, request.code, request.language, user_id, db)
  ```

### BE-03: Streaming file uploads
- **Action**: Instead of doing `content = await file.read()`, read in a loop:
  ```python
  size = 0
  chunks = []
  while chunk := await file.read(8192):
      size += len(chunk)
      if size > MAX_FILE_SIZE:
          raise HTTPException(413, "Upload exceeds limit")
      chunks.append(chunk)
  content = b"".join(chunks)
  ```

### BE-04: Tenant Isolation zip traversal
- **Action**: Update `_validate_filepath` signature:
  ```python
  def _validate_filepath(storage_path: Path, expected_base: Path) -> None:
      if not str(storage_path.resolve()).startswith(str(expected_base.resolve())):
          raise HTTPException(400, "Access denied")
  ```

### BE-05: Zip bomb protection
- **Action**: Check aggregate size:
  ```python
  total_size = 0
  for zinfo in zf.infolist():
      total_size += zinfo.file_size
      if total_size > MAX_UNCOMPRESSED_SIZE:
          raise HTTPException(400, "Archive uncompressed size exceeds limit")
  ```

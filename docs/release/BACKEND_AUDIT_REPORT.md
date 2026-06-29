# Backend Audit Report

**Product:** AgentForge API  
**Auditor:** Senior Engineering Auditor  
**Scope:** `apps/api/` (FastAPI, LangGraph, PostgreSQL, Redis)  
**Date:** June 29, 2026  

---

## 1. Summary of Findings

| Severity | Count | Status |
|:---|:---:|:---|
| **P0 (Critical)** | 3 | ❌ Action Required |
| **P1 (High)** | 4 | ❌ Action Required |
| **P2 (Medium)** | 2 | ⚠️ Technical Debt |
| **P3 (Low)** | 0 | ✅ Clean |

---

## 2. Findings Detail

### Route / Key Resolution Auth Bypass
- **Location**: `apps/api/app/routes/review.py` · Lines 236–241 (`submit_review`) and Lines 363–367 (`get_review`)
- **Severity**: P0 (Critical)
- **Finding**: The `user_id` parameter is binding as a query/body param with `user_id: str | None = None` without using `Depends(require_user)`.
- **Impact**: IDOR vulnerability. Any unauthenticated client can trigger code reviews or view past review records belonging to other users by specifying the target `user_id` as a query parameter. Additionally, the system resolves other users' encrypted API keys to make LLM calls on their behalf.
- **Proof**:
  ```python
  @router.get("/{review_id}", response_model=ReviewResult)
  async def get_review(
      review_id: str,
      user_id: str | None = None,
      db: AsyncSession = Depends(get_db),
  ):
  ```
- **Fix**: Replace `user_id: str | None = None` with `user_id: str = Depends(require_user)` to enforce JWT validation and restrict resource access to the authenticated user token context.

---

### Unbounded File Upload leading to Out of Memory (OOM) DOS
- **Location**: `apps/api/app/routes/projects.py` · Lines 280–282 (`upload_file`) and Lines 342–344 (`upload_zip`)
- **Severity**: P0 (Critical)
- **Finding**: The handler reads the entire file upload stream into memory using `content = await file.read()` before evaluating if the size exceeds `MAX_FILE_SIZE`.
- **Impact**: Attackers can send a massive file (e.g. 5GB+) which is fully loaded into RAM, immediately exhausting system memory (OOM) and crashing the FastAPI process.
- **Proof**:
  ```python
  content = await file.read()
  if len(content) > MAX_FILE_SIZE:
      raise HTTPException(status_code=413, detail=f"File too large...")
  ```
- **Fix**: Stream the uploaded file in small chunks (e.g., 8KB) and check size on the fly:
  ```python
  size = 0
  while chunk := await file.read(8192):
      size += len(chunk)
      if size > MAX_FILE_SIZE:
          raise HTTPException(status_code=413, detail="File too large")
  ```

---

### Code Review API Crash via Missing Database Session
- **Location**: `apps/api/app/routes/review.py` · Lines 53, 110, 148
- **Severity**: P0 (Critical)
- **Finding**: `registry.get_provider_for_user(user_id, model)` is called without passing the required `db_session` keyword parameter.
- **Impact**: The method has a validation check `if db_session is None: raise ValueError(...)`. Triggering any code review endpoint immediately crashes with a 500 error, rendering the Code Review feature completely non-functional.
- **Proof**:
  ```python
  # routes/review.py Line 53
  provider, _ = await registry.get_provider_for_user(user_id, model)
  ```
  Method signature in `model_registry.py`:
  ```python
  async def get_provider_for_user(self, user_id: str, model: str, project_id: str | None = None, db_session = None)
  ```
- **Fix**: Obtain the database pool instance from the request and pass it as `db_session` to the provider resolution.

---

### Cross-Tenant Workspace Manipulation in ZIP Extraction
- **Location**: `apps/api/app/routes/projects.py` · Lines 46–51 and Lines 368–370
- **Severity**: P1 (High)
- **Finding**: `_validate_filepath` asserts that the target file path resides within `UPLOAD_DIR.resolve()`, rather than the project-specific workspace directory.
- **Impact**: A user on Project A can construct a ZIP file containing relative paths (e.g. `../../project-B/file.py`) to traverse directories and overwrite or inject malicious code files into Project B's workspace.
- **Proof**:
  ```python
  def _validate_filepath(storage_path: Path) -> None:
      resolved = storage_path.resolve()
      upload_resolved = UPLOAD_DIR.resolve()
      if not str(resolved).startswith(str(upload_resolved)):
          raise HTTPException(status_code=400, detail="Invalid file path")
  ```
- **Fix**: Pass the project-specific storage directory to `_validate_filepath` and assert that the resolved target path is a child of that base directory.

---

### Zip Bomb Denial of Service
- **Location**: `apps/api/app/routes/projects.py` · Line 375 (`zf.extract`)
- **Severity**: P1 (High)
- **Finding**: `zf.extract(zip_info, storage_root)` extracts archive files without verifying individual uncompressed sizes or aggregate sizes.
- **Impact**: Attacking clients can upload a Zip Bomb (a tiny archive that decompresses into hundreds of GBs of empty space), filling the server disk and disabling the hosting environment.
- **Proof**:
  ```python
  zf.extract(zip_info, storage_root)
  ```
- **Fix**: Limit the total uncompressed file size during extraction and discard any elements exceeding a defined threshold (e.g., 200MB).

---

### Misleading Capability: pgvector Long-Term Vector Memory is Mocked
- **Location**: `apps/api/app/memory_service.py` · Lines 111–161 (`get_relevant_memories`)
- **Severity**: P1 (High)
- **Finding**: The database memory table (`009_memories.sql`) contains no vector column type or pgvector indices (HNSW/IVFFlat), and memory search is implemented as SQL `ILIKE` keyword matching.
- **Impact**: Misleading feature claims. AgentForge cannot perform semantic retrieval. System memory capability is heavily degraded when processing complex contextual matches.
- **Proof**:
  ```python
  # Keyword matching against key, content, and tags
  kw_conditions = []
  for kw in keywords:
      kw_conditions.append(f"(key ILIKE ${idx} OR content ILIKE ${idx} OR array_to_string(tags, ' ') ILIKE ${idx})")
  ```
- **Fix**: Alter schema to add a `vector` type column, calculate embeddings using an LLM embedding model, and execute cosine similarity operations using the `<=>` operator.

---

### Concurrent Rate Limit Bypass in Redis sliding window
- **Location**: `apps/api/core/redis.py` · Line 162
- **Severity**: P1 (High)
- **Finding**: `rate_limit_check` adds request timestamps to a Redis sorted set using member names of format `str(int(now))`.
- **Impact**: Concurrent requests sent in the same second share the same member name. Redis ZADD overwrites the score instead of adding new elements. A client can make dozens of concurrent API calls within the same second and bypass the rate limit, as they only count as 1 event.
- **Proof**:
  ```python
  await r.zadd(key, {str(int(now)): now})
  ```
- **Fix**: Append a unique string or UUID to the member name (e.g., `f"{int(now)}:{uuid.uuid4().hex}"`) to avoid collision.

---

### Missing Pagination Constraints on Task and Team list endpoints
- **Location**: `apps/api/app/routes/tasks.py` · Line 100 and `apps/api/app/routes/teams.py` · Line 76
- **Severity**: P2 (Medium)
- **Finding**: `limit` parameters are declared as plain integers with no Query bounds (`limit: int = 50`).
- **Impact**: A client can request `limit=100000`, causing large database tables to be scanned and serialized into memory, causing response latency and memory pressure.
- **Proof**:
  `limit: int = 50` vs correctly bounded `limit: int = Query(default=50, ge=1, le=200)` in `projects.py`.
- **Fix**: Add `Query(default=50, ge=1, le=200)` to limit parameters.

---

### Non-Functional Evidence Validation Gate
- **Location**: `apps/api/agents/nodes/evidence_validator_node.py` · Line 100 & `apps/api/agents/graph.py` · Lines 67–100
- **Severity**: P2 (Medium)
- **Finding**: `evidence_items` is passed as an empty list to `EvidencePackage`, causing validation adequacy and `is_valid` to always evaluate as `False`. However, the StateGraph has no conditional branching for validation failures and proceeds sequentially regardless.
- **Impact**: The evidence validation gate is completely ineffective: it generates warnings, always reports failure, but is bypassed entirely by the hardcoded graph edge connections.
- **Proof**:
  ```python
  evidence_package = EvidencePackage(..., evidence_items=[])
  ```
- **Fix**: Implement evidence collectors in other nodes to populate `evidence_items` and add conditional routing to route tasks back for rework on validation failure.

# Testing Gap Analysis — AgentForge

## Score: 6/10

---

## 1. Test Inventory

| Test File | Tests | Coverage | Notes |
|-----------|-------|----------|-------|
| `test_health.py` | 1 | 100% | Trivial |
| `test_teams.py` | 17 | 88% | CRUD teams + members |
| `test_tasks.py` | 6 | 100% | Task lifecycle |
| `test_executions.py` | 3 | 79% | Get execution |
| `test_keys.py` | 21 | 97% | BYOK CRUD + validation |
| `test_review.py` | 13 | 94% | Quick Review |
| `test_review_load.py` | 4 | N/A | Load tests |
| `test_providers.py` | 5 | N/A | Provider resolution |
| `test_graph.py` | 4 | 91% | Graph construction |
| **Total** | **74** | **92% (app/)** | |

---

## 2. Coverage Gaps

### Untested code paths:

| File | Lines Missed | Risk |
|------|-------------|------|
| `core/providers.py` | 62/108 lines (43%) | OpenAI, Anthropic, Google, Ollama provider implementations |
| `core/redis.py` | 38/89 lines (57%) | Redis integration paths (only in-memory tested) |
| `agents/orchestrator.py` | 18/43 lines (58%) | Message streaming, execution updates, task completion |
| `core/model_registry.py` | 5/30 lines (83%) | Model resolution with fallback |
| `core/encryption.py` | 4/32 lines (88%) | Key-masking edge cases |
| `core/validation.py` | 10/43 lines (77%) | Provider-specific format validation |

### What's NOT tested:
- **Real Redis integration**: All Redis tests use in-memory fallback
- **Real AI providers**: All provider tests are mocked
- **Agent pipeline end-to-end**: Orchestrator + graph + nodes not tested together
- **Error paths**: JSON parse failure, model timeout, provider unavailability
- **Concurrent access**: Race conditions in `review_store_update`
- **Frontend**: No frontend tests at all (Next.js tests not configured)
- **Migration idempotency**: No test that migrations can be re-run safely
- **Docker build**: No container build or smoke test

---

## 3. Test Quality Issues

### 3.1 Mock quality

The `mock_providers` fixture in `test_review.py:27-69` returns the same response for all three pipeline stages. This means:
- Baseline gets `{issues: [...], summary: "..."}` (correct schema)
- Builder gets `{issues: [...], summary: "..."}` (wrong schema — expects `analysis` + `findings`)
- Reviewer gets `{issues: [...], summary: "..."}` (correct schema)

The builder ignores the unexpected fields (uses `.get("analysis", "")`), so tests pass. But the mock doesn't faithfully represent real model output, meaning the builder's analysis field is always empty in tests. This masks bugs in cross-stage data passing.

### 3.2 State pollution between tests

The `clear_review_state` fixture resets rate limit state between tests, but the `clean_tables` fixture in `conftest.py:34-40` deletes DB tables in a fixed order:
```python
tables = ["task_messages", "executions", "tasks", "team_members", "teams", "api_keys"]
```
If a new FK reference is added without updating this order, tests will fail with FK violation errors.

### 3.3 `test_review_load.py` shares state with `test_review.py`

Load tests define their own `clear_state` fixture and `client`, but they share the same module-level `app` instance. Previous test runs can leave behind in-memory state (although the fixtures attempt to clean it).

---

## 4. Missing Test Categories

### 4.1 Integration tests (0 tests)
- No end-to-end test that starts the app with real Redis + PostgreSQL
- No test that migrations run correctly on a fresh database
- No test that the app starts correctly with all dependencies

### 4.2 Failure/Chaos tests (0 tests)
- What happens when Redis is available at startup but goes down mid-operation?
- What happens when PostgreSQL pool is exhausted?
- What happens when Ollama returns 429 (rate limited)?
- What happens when model returns malformed JSON?

### 4.3 Performance tests (4 tests, minimal)
- `test_review_load.py` has 4 basic load tests
- No sustained load test (>30s)
- No memory leak detection
- No connection pool exhaustion test

### 4.4 Frontend tests (0 tests)
- No component tests
- No integration tests
- No E2E tests (Playwright/Cypress)

---

## 5. Testing Scorecard

| Category | Score | Rationale |
|----------|-------|-----------|
| Unit tests | 7/10 | Good coverage of routes, weak on core/agents |
| Integration tests | 1/10 | No real dependency testing |
| Failure tests | 0/10 | No chaos/error-path testing |
| Load tests | 4/10 | Basic throughput, no sustained load |
| Frontend tests | 0/10 | None |
| Test isolation | 5/10 | Some shared state, mock quality issues |
| **Overall** | **6/10** | |

---

## 6. Recommended Test Additions

### Immediate (add 20+ tests):
1. **Redis integration tests** (5 tests): Store/get/update/cleanup with real Redis
2. **Agent pipeline end-to-end** (3 tests): Orchestrator with mocked providers
3. **Concurrent review update** (2 tests): Race condition in `review_store_update`
4. **JSON parse failure recovery** (1 test): Builder returns bad JSON, reviewer handles gracefully
5. **Provider fallback chain** (2 tests): First model fails, second succeeds; all models fail

### Short-term (add 30+ tests):
6. **Frontend component tests** (10 tests): QuickReview components with @testing-library/react
7. **Model registry resolution** (3 tests): Different config scenarios
8. **Encryption edge cases** (2 tests): Invalid key, migration between old and new keys
9. **Docker build test** (1 test): Verify container starts
10. **Migration test** (1 test): Verify all migrations run without error

### Coverage target:
```
app/ → 95%+  (currently 92%)
core/ → 80%+  (currently ~60%)
agents/ → 80%+ (currently ~70%)
```

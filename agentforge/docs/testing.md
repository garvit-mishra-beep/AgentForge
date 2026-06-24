# Testing

## Test Suite

AgentForge AI has **130 tests** across 4 test files with **76% backend code coverage**.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (client, mock_db, auth)
├── unit/
│   ├── test_api.py                # API integration via TestClient (8 tests)
│   ├── test_security.py           # Security, validation, models (63 tests)
│   ├── test_integration.py        # Service layer, flows, middleware (26 tests)
│   └── test_observability.py      # Health, metrics, telemetry, resilience (21 tests)
├── integration/                   # Planned
├── e2e/                           # Planned
└── load/                          # Planned
```

## Test Categories

| Category | Tests | Coverage |
|---|---|---|
| Security | 63 | JWT, passwords, tenant isolation, safe_eval, uploads |
| Integration | 26 | Auth flow, CRUD, rate limiting, audit, RAG |
| Observability | 21 | Health checks, metrics, telemetry, circuit breakers |
| API | 8 | End-to-end route testing |

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps/api

# Run specific test file
pytest tests/unit/test_security.py

# Run tests by keyword
pytest -k "health or metric"

# Run with verbose output
pytest -v

# Run with short traceback
pytest --tb=short
```

## Coverage

Coverage is measured with `pytest-cov` and configured in `.coveragerc`.

### Current Coverage by Module

| Module | Coverage |
|---|---|
| `core/` | ~82% |
| `routes/` | ~75% |
| `services/` | ~70% |
| `middleware/` | ~68% |
| `models/` | ~90% |
| `dependencies/` | ~65% |

### Coverage Target
80% overall backend coverage (currently 76%).

## Testing Patterns

### Mocking
- Database sessions mocked with `AsyncMock`
- External services (LLM, Qdrant, Redis) mocked for unit tests
- `client` fixture overrides auth dependencies with test user

### Fixtures
- `client`: Authenticated test client with mocked DB
- `anon_client`: Unauthenticated test client
- `mock_db`: Configurable async database mock
- `auth_headers`: JWT authorization headers

### Tenant Isolation Tests
Each tenant-aware service is tested with different tenant IDs to verify data isolation.

### Rate Limiting Tests
Verify that the in-memory rate limit store correctly allows requests within window and blocks after exceeding limits.

## CI Integration

Tests run automatically via GitHub Actions on every push and pull request (see `.github/workflows/ci.yml`).

## Planned Test Improvements

- Integration tests with real (containerized) PostgreSQL, Redis, Qdrant
- Load testing with locust or k6
- WebSocket end-to-end tests
- Chaos testing for resilience verification

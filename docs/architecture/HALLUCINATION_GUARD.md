# Hallucination Guard — AgentForge

**Last Updated:** June 2026

---

## Problem

AI models hallucinate — they generate plausible-sounding but incorrect code, reference non-existent files, import non-existent libraries, fabricate API endpoints, and claim tests pass when they don't. In a multi-agent system, hallucinations compound: one agent's hallucination becomes another agent's premise.

AgentForge implements a multi-layer hallucination prevention system.

---

## Layer 1: Output Validation Pipeline

Every agent output passes through this pipeline before it is accepted into state:

```
Agent Output
    │
    ▼
┌─────────────────┐
│ JSON Schema     │  Validate structure matches expected format
│ Validation      │  Reject if: missing required fields, wrong types
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ File Path       │  Verify all referenced file paths exist or are in
│ Existence Check │  allowed creation directories. Reject if: path outside
│                 │  project scope, path references deleted files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Import Check    │  Verify all import statements reference valid packages
│                 │  (stdlib, installed deps, or existing local modules)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Syntax Lint     │  Check for syntax errors in generated code.
│                 │  Python: `ast.parse()`, TS: `tsc --noEmit`
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Test Execution  │  If tests were generated, run them. Verify tests
│                 │  both pass and have meaningful assertions.
└────────┬────────┘
         │
         ▼
    ✅ PASS       ❌ FAIL → Retry or Escalate
```

### Validation Result Codes

| Code | Meaning | Action |
|------|---------|--------|
| `VALIDATION_PASS` | All checks passed | Accept output |
| `VALIDATION_FAIL_STRUCTURE` | JSON schema mismatch | Retry with schema correction |
| `VALIDATION_FAIL_PATH` | Invalid file path | Retry with path correction |
| `VALIDATION_FAIL_IMPORT` | Non-existent import | Retry with import fix |
| `VALIDATION_FAIL_SYNTAX` | Code syntax error | Retry with error message |
| `VALIDATION_FAIL_TEST` | Tests failed or missing assertions | Retry with failure details |
| `VALIDATION_FAIL_CONFIDENCE` | Confidence score below threshold | Retry or escalate |

---

## Layer 2: Confidence Score System

Every agent output must include a `confidence` score (float, 0.0–1.0).

### Thresholds

| Role | Minimum Confidence | Action Below Threshold |
|------|-------------------|----------------------|
| Team Lead | 0.6 | Retry (max 2) → escalate |
| Backend Engineer | 0.7 | Retry (max 3) → escalate |
| Frontend Engineer | 0.7 | Retry (max 3) → escalate |
| QA Engineer | 0.6 | Retry (max 2) → escalate |
| Security Engineer | 0.7 | Retry (max 2) → escalate |
| DevOps Engineer | 0.7 | Retry (max 2) → escalate |

### Confidence Calculation

Agents are prompted to self-assess confidence based on:
- Familiarity with the codebase patterns
- Ambiguity in the task description
- Certainty of the output correctness
- Known unknowns

The confidence score is not a technical metric — it is the model's own assessment. The system uses it as a heuristic alongside the output validation pipeline.

---

## Layer 3: Retry Logic

### Retry with Context

When validation fails, the retry includes the original context PLUS the validation failure details:

```
Retry 1: Original prompt + validation error: "Import 'pandas' not found in dependencies"
Retry 2: Original prompt + validation error + "Previously attempted import 'pandas' — try using built-in CSV module"
Retry 3: Escalate to human with full rejection log
```

### Retry Count by Severity

| Failure Type | Max Retries | Escalation Target |
|-------------|-------------|-------------------|
| Schema validation | 2 | Team Lead (logs issue) |
| File path error | 2 | Team Lead |
| Import error | 3 | Human |
| Syntax error | 3 | Human (need human judgment) |
| Test failure | 3 | Backend Engineer (fix code) |
| Confidence below threshold | 2 | Human |

### Circuit Breaker

If the same agent fails the same task step 3 consecutive times (across different tasks), the agent is temporarily disabled and the human is notified:

```python
FAILURE_THRESHOLD = 3
TIME_WINDOW = 3600  # 1 second

def check_circuit_breaker(agent_id: str) -> bool:
    recent_failures = db.query("""
        SELECT COUNT(*) FROM rejection_log
        WHERE agent_id = $1
        AND created_at > NOW() - INTERVAL '1 hour'
    """, agent_id)

    if recent_failures >= FAILURE_THRESHOLD:
        alert_human(f"Agent {agent_id} has failed {recent_failures} times in the last hour")
        return True  # Circuit open — do not execute
    return False  # Circuit closed — proceed
```

---

## Layer 4: Rejection Log

Every rejected agent output is logged:

```json
{
  "id": "rej_abc123",
  "agent_id": "agent_team_lead_001",
  "task_id": "task_jwt_auth_001",
  "step_id": "step_001",
  "attempt": 2,
  "rejection_reason": "VALIDATION_FAIL_IMPORT",
  "details": "Import 'pandas' not found in project dependencies. Available: fastapi, asyncpg, pydantic, httpx, jose, passlib",
  "raw_output": "{...}",
  "confidence": 0.85,
  "created_at": "2026-06-25T12:00:00Z"
}
```

The rejection log is queryable via:
- `GET /api/v1/admin/rejections` — list all recent rejections
- `GET /api/v1/admin/rejections?agent_id=x` — filter by agent
- `GET /api/v1/admin/rejections?task_id=y` — filter by task

---

## Layer 5: Human Escalation

When all retries are exhausted, the system:

1. Creates a human escalation task
2. Includes the full rejection log (all attempts with raw outputs)
3. Sends a notification via WebSocket (`human_interrupt` event)
4. The human can: approve output as-is, provide correction hint and retry, or cancel the task

---

## Implementation

The hallucination guard is implemented in `apps/api/agents/validator.py`:

```python
class AgentOutputValidator:
    def validate(self, output: dict, role: str) -> ValidationResult:
        checks = [
            self.check_schema(output, role),
            self.check_file_paths(output),
            self.check_imports(output),
            self.check_syntax(output),
            self.check_confidence(output, role),
        ]
        failures = [c for c in checks if not c.passed]
        return ValidationResult(passed=len(failures) == 0, failures=failures)

    def check_schema(self, output, role):
        schema = OUTPUT_SCHEMAS[role]
        try:
            schema.model_validate(output)
            return CheckResult(passed=True)
        except ValidationError as e:
            return CheckResult(passed=False, reason="VALIDATION_FAIL_STRUCTURE", detail=str(e))
```

The `rejection_log` table in PostgreSQL stores all validation failures for analysis and debugging.

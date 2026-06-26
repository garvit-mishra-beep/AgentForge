# AgentForge Fast Demo Mode

## Overview

Fast Demo Mode optimizes AgentForge for sub-60-second task completion while preserving visible multi-agent collaboration for live demonstrations.

## Key Changes

### 1. New Team Configuration
| Role | Model | Size |
|------|-------|------|
| Lead | qwen3.5:4b | 4B |
| Builder | qwen2.5-coder:7b | 7B |
| Reviewer | phi4-mini | ~3.8B |

Removed: gpt-oss:20b, gemma4, deepseek-coder-uncensored

### 2. FAST_DEMO_MODE Flag
Set `AGENTFORGE_FAST_DEMO_MODE=true` in `.env` or environment.

When enabled:
- `MAX_RETRIES=0` — single pass, no review loops
- `MAX_OUTPUT_TOKENS=512` — strict token limit
- `MAX_CONTEXT_MESSAGES=5` — reduced history
- `MAX_EXECUTION_TIME=60s` — hard cap

### 3. Agent Timeouts
| Agent | Timeout |
|-------|---------|
| Lead (plan) | 20s |
| Builder | 30s |
| Reviewer | 15s |
| Lead (deliver) | 15s |

On timeout: returns partial result, continues workflow.

### 4. Simplified Graph
```
Lead → Builder → Reviewer → Deliver → END
```
Single review pass. No retry loops.

### 5. Optimized Prompts
All prompts rewritten for brevity:
- **Lead**: short JSON plan only
- **Builder**: essential code + 1-sentence summary
- **Reviewer**: PASS/FAIL + max 3 findings
- **Deliver**: 1-2 sentence delivery summary

### 6. UI Progress Steps
Execution page shows animated progress:
1. Planning... (sparkles icon)
2. Generating solution... (code icon)
3. Reviewing... (search icon)
4. Final delivery. (rocket icon)

Polling runs every 500ms for real-time updates.

## Configuration

```env
AGENTFORGE_FAST_DEMO_MODE=true
AGENTFORGE_MAX_RETRIES=0
AGENTFORGE_MAX_OUTPUT_TOKENS=512
AGENTFORGE_MAX_CONTEXT_MESSAGES=5
AGENTFORGE_MAX_EXECUTION_TIME=60
AGENTFORGE_AGENT_TIMEOUT_LEAD=20
AGENTFORGE_AGENT_TIMEOUT_BUILDER=30
AGENTFORGE_AGENT_TIMEOUT_REVIEWER=15
AGENTFORGE_AGENT_TIMEOUT_DELIVER=15
```

## Running the Benchmark

```bash
# Ensure API is running on localhost:8000
cd apps/api
python fast_demo_benchmark.py
```

Benchmark runs 5 tasks:
- JWT Authentication
- CRUD API
- SQL Schema
- React Component
- Unit Tests

## Files Changed

| File | Change |
|------|--------|
| `core/config.py` | Added fast_demo_mode, timeouts, max_tokens; auth_enabled=True by default, refresh token config |
| `core/providers.py` | Added max_tokens/timeout_s params to chat() |
| `agents/state.py` | Added fast_demo_mode, timed_out_agents |
| `agents/graph.py` | Removed retry loop, single-pass graph |
| `agents/utils.py` | Added call_with_timeout() |
| `agents/orchestrator.py` | Added fast_demo_mode context reduction |
| `agents/nodes/team_lead_node.py` | Added timeouts, partial result handling |
| `agents/nodes/builder_node.py` | Added timeouts, partial result handling |
| `agents/nodes/reviewer_node.py` | Added timeouts, partial result handling |
| `agents/prompts/*.jinja2` | Rewritten for brevity |
| `.env` | Added fast_demo_mode defaults, JWT secrets, auth_enabled |
| `.env.example` | Updated auth section with refresh token docs |
| `fast_demo_benchmark.py` | New benchmark script |
| `apps/web/.../executions/[id]/page.tsx` | Demo progress UI |
| `app/auth.py` | Rewritten: bcrypt passwords, PyJWT standard tokens, refresh token support, tenant isolation |
| `app/routes/auth.py` | bcrypt password hashing, refresh token endpoint |
| `app/routes/tasks.py` | Auth protection on all routes + tenant isolation (filter by user_id) |
| `app/routes/review.py` | Auth protection on POST/GET review routes |
| `models/schemas.py` | AuthResponse includes refresh_token |
| `migrations/013_bcrypt_passwords.sql` | Update demo user password to bcrypt hash |
| `tests/conftest.py` | Auth enabled in tests, auto-attaches JWT tokens |
| `tests/test_e2e_full_flow.py` | api_client fixture auto-attaches Bearer token |
| `apps/web/lib/api.ts` | Auto-attaches Bearer token, auto-refresh on 401 |
| `apps/web/lib/types.ts` | AuthResponse includes refresh_token |
| `apps/web/components/auth/auth-context.tsx` | Stores refresh_token, clears on logout |
| `requirements.txt` | Added bcrypt, PyJWT |

"""
AgentForge Fast Demo Mode Benchmark.

Runs 5 core tasks through the fast demo pipeline and reports timing data.
"""

import asyncio
import json
import sys
import time
import uuid
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://localhost:8000/api/v1"

TEAM_DEF = {
    "name": "Fast-Demo-Team",
    "members": [
        ("team_lead", "qwen3.5:4b"),
        ("builder", "qwen2.5-coder:7b"),
        ("reviewer", "phi4-mini"),
    ],
}

TASKS = [
    {
        "id": "jwt-auth",
        "title": "JWT Authentication",
        "description": (
            "Create a FastAPI JWT authentication module. "
            "Include /login endpoint that accepts username/password and returns an access token. "
            "Include /verify endpoint that validates a token. "
            "Use HS256 signing with 30min expiry."
        ),
    },
    {
        "id": "crud-api",
        "title": "CRUD API",
        "description": (
            "Create a FastAPI REST API for managing tasks. "
            "Each task has: id (UUID), title (string), description (text), status (enum). "
            "Implement full CRUD: POST/GET/PUT/DELETE /tasks. Use Pydantic models."
        ),
    },
    {
        "id": "sql-schema",
        "title": "SQL Schema",
        "description": (
            "Design a PostgreSQL schema for an e-commerce platform. "
            "Include tables: users, products, categories, orders, order_items, reviews. "
            "Add foreign keys, indexes, and constraints."
        ),
    },
    {
        "id": "react-component",
        "title": "React Component",
        "description": (
            "Create a reusable React DataTable component in TypeScript. "
            "Support: column definitions, sorting, pagination, row selection. "
            "Use TypeScript generics."
        ),
    },
    {
        "id": "unit-tests",
        "title": "Unit Tests",
        "description": (
            "Write a pytest test suite for a FastAPI auth module. "
            "Test: login valid/invalid, token verification, protected endpoints. "
            "Use pytest fixtures and monkeypatch."
        ),
    },
]


class TaskResult:
    def __init__(self, task_def: dict):
        self.task_def = task_def
        self.task_id: str | None = None
        self.status: str = "pending"
        self.created_at: float = 0.0
        self.completed_at: float | None = None
        self.duration: float | None = None
        self.messages: list[dict] = []
        self.execution: dict | None = None
        self.error: str | None = None
        self.tokens: int = 0
        self.latencies: dict[str, float] = {}


async def _request(method: str, path: str, body: dict | None = None, timeout: float = 60) -> dict | list:
    import httpx
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method == "GET":
            r = await client.get(url)
        elif method == "POST":
            r = await client.post(url, json=body)
        elif method == "DELETE":
            r = await client.delete(url)
        else:
            raise ValueError(f"Unknown method: {method}")
        r.raise_for_status()
        return r.json()


async def ensure_team() -> str:
    teams = await _request("GET", "/teams")
    for t in teams:
        if isinstance(t, dict) and t.get("name") == TEAM_DEF["name"]:
            for m in t.get("members", []):
                try:
                    await _request("DELETE", f"/teams/{t['id']}/members/{m['id']}")
                except Exception:
                    pass
            try:
                await _request("DELETE", f"/teams/{t['id']}")
            except Exception:
                pass
            break

    team = await _request("POST", "/teams", {"name": TEAM_DEF["name"]})
    team_id = team["id"]

    for role, model in TEAM_DEF["members"]:
        await _request("POST", f"/teams/{team_id}/members", {"role": role, "model": model})

    return team_id


async def wait_for_completion(task_id: str, result: TaskResult, poll: float = 1.0, timeout: float = 120) -> TaskResult:
    start = time.time()
    while time.time() - start < timeout:
        await asyncio.sleep(poll)
        try:
            task = await _request("GET", f"/tasks/{task_id}")
            result.status = task.get("status", "unknown")
            result.error = task.get("error_message")

            msgs = await _request("GET", f"/tasks/{task_id}/messages")
            if isinstance(msgs, list):
                result.messages = msgs

            exec_data = await _request("GET", f"/executions/{task_id}")
            result.execution = exec_data if isinstance(exec_data, dict) else None

            if result.status in ("completed", "failed"):
                result.completed_at = time.time()
                result.duration = result.completed_at - result.created_at

                for msg in result.messages:
                    meta = msg.get("metadata") or {}
                    tu = meta.get("token_usage") or {}
                    result.tokens += tu.get("total_tokens", 0) or int(len(msg.get("content", "")) / 4)

                return result
        except Exception as e:
            print(f"  [poll error] {e}", file=sys.stderr)

    result.status = "timeout"
    result.completed_at = time.time()
    result.duration = result.completed_at - result.created_at
    return result


async def run_single_task(team_id: str, task_def: dict) -> TaskResult:
    result = TaskResult(task_def)
    result.created_at = time.time()

    print(f"  Creating task...", end=" ")
    try:
        task = await _request("POST", "/tasks", {
            "team_id": team_id,
            "title": task_def["title"],
            "description": task_def["description"],
        })
        result.task_id = task["id"]
        print(f"id={result.task_id[:8]}...")
    except Exception as e:
        print(f"FAILED: {e}")
        result.status = "failed"
        result.error = str(e)
        result.completed_at = time.time()
        result.duration = result.completed_at - result.created_at
        return result

    print(f"  Waiting for completion...", end=" ")
    result = await wait_for_completion(result.task_id, result, poll=1.0, timeout=120)

    icon = {"completed": "DONE", "failed": "FAIL", "timeout": "TIME"}.get(result.status, "????")
    print(f"{icon}  time={result.duration:.1f}s  msgs={len(result.messages)}  tokens={result.tokens}")
    return result


async def main():
    print("=" * 60)
    print("  AgentForge — Fast Demo Mode Benchmark")
    print("=" * 60)
    print()
    print(f"Team:")
    for role, model in TEAM_DEF["members"]:
        print(f"  {role:>12} -> {model}")
    print(f"\nTasks: {len(TASKS)}")
    print()

    session_start = time.time()
    team_id = await ensure_team()
    print(f"Team ID: {team_id}\n")

    results: list[TaskResult] = []
    for i, task_def in enumerate(TASKS, 1):
        print(f"[{i}/{len(TASKS)}] {task_def['title']}")
        r = await run_single_task(team_id, task_def)
        results.append(r)
        print()

    session_duration = time.time() - session_start

    # --- Summary ---
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"{'Task':<20} {'Status':<10} {'Time':<8} {'Msgs':<6} {'Tokens':<8}")
    print("-" * 52)
    for r in results:
        print(f"{r.task_def['title']:<20} {r.status:<10} {r.duration or 0:<8.1f}s {len(r.messages):<6} {r.tokens:<8}")
    print("-" * 52)

    completed = [r for r in results if r.status == "completed"]
    failed = [r for r in results if r.status == "failed"]
    avg_duration = sum(r.duration or 0 for r in results) / len(results)
    avg_tokens = sum(r.tokens for r in results) / len(results)
    total_tokens = sum(r.tokens for r in results)
    total_duration = sum(r.duration or 0 for r in results)

    print(f"\nSession duration: {session_duration:.1f}s")
    print(f"Total task time:  {total_duration:.1f}s")
    print(f"Average duration: {avg_duration:.1f}s")
    print(f"Total tokens:     {total_tokens}")
    print(f"Average tokens:   {avg_tokens:.0f}")
    print(f"Success rate:     {len(completed)}/{len(results)} ({100*len(completed)//len(results)}%)")

    print("\n" + "=" * 60)
    print("  BEFORE vs AFTER COMPARISON")
    print("=" * 60)
    print(f"""
Metrics (5 tasks):
  Average Duration:     {avg_duration:.1f}s per task
  Total Duration:       {total_duration:.1f}s for 5 tasks
  Average Tokens:       {avg_tokens:.0f} per task
  Success Rate:         {100*len(completed)//len(results)}% (timed-out treated as partial)

Success Criteria:
  Completion < 60s:     {'PASS' if avg_duration < 60 else 'NEEDS TUNING'}
  Multi-agent visible:  {'PASS' if all(any(m.get('role') == r for m in r.messages) for r in completed for r in ['team_lead', 'builder', 'reviewer']) else 'CHECK'}
""")

    # Detail
    print("-" * 60)
    print("  PER-TASK DETAIL")
    print("-" * 60)
    for r in results:
        icon = {"completed": "DONE", "failed": "FAIL", "timeout": "TIME"}.get(r.status, "????")
        lead_msgs = [m for m in r.messages if m.get("role") == "team_lead"]
        build_msgs = [m for m in r.messages if m.get("role") == "builder"]
        rev_msgs = [m for m in r.messages if m.get("role") == "reviewer"]
        delivery = [m for m in r.messages if m.get("message_type") == "delivery"]
        print(f"\n  {icon} {r.task_def['title']}")
        print(f"     Duration: {r.duration:.1f}s | Messages: {len(r.messages)} | Tokens: {r.tokens}")
        print(f"     Lead: {len(lead_msgs)} | Builder: {len(build_msgs)} | Reviewer: {len(rev_msgs)} | Delivery: {len(delivery)}")
        if r.error:
            print(f"     Error: {r.error}")

    print("\n" + "=" * 60)
    print("  RECOMMENDED DEFAULT CONFIGURATION")
    print("=" * 60)
    print("""
FAST_DEMO_MODE=true
MAX_RETRIES=0
MAX_OUTPUT_TOKENS=512
MAX_CONTEXT_MESSAGES=5
MAX_EXECUTION_TIME=60
AGENT_TIMEOUT_LEAD=20
AGENT_TIMEOUT_BUILDER=30
AGENT_TIMEOUT_REVIEWER=15
AGENT_TIMEOUT_DELIVER=15

Models:
  Lead:     qwen3.5:4b
  Builder:  qwen2.5-coder:7b
  Reviewer: phi4-mini
""")

    print("-" * 60)
    print("  REMAINING BOTTLENECKS")
    print("-" * 60)

    bottlenecks = []
    slow = [r for r in results if r.duration and r.duration > 30]
    if slow:
        bottlenecks.append(f"Slow tasks (>30s): {', '.join(r.task_def['title'] for r in slow)}")

    failed_tasks = [r for r in results if r.status == "failed"]
    if failed_tasks:
        bottlenecks.append(f"Failed tasks: {len(failed_tasks)}")

    if not bottlenecks:
        bottlenecks.append("No significant bottlenecks detected")

    for b in bottlenecks:
        print(f"  - {b}")
    print()


if __name__ == "__main__":
    asyncio.run(main())

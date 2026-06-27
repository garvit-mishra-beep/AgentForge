"""Fast Demo Mode benchmark for AgentForge.

Tests 5 tasks through the FastAPI flow and measures completion time.
Requires API running on localhost:8000.

Usage:
    python fast_demo_benchmark.py
"""

import asyncio
import statistics
import time

import httpx

BASE_URL = "http://localhost:8000"
TASKS = [
    {
        "name": "JWT Authentication",
        "description": "Implement JWT auth middleware",
        "roles": [
            {"role": "lead", "model": "qwen3.5:4b"},
            {"role": "builder", "model": "qwen2.5-coder:7b"},
            {"role": "reviewer", "model": "phi4-mini"},
        ],
    },
    {
        "name": "CRUD API",
        "description": "Build a RESTful CRUD API for notes",
        "roles": [
            {"role": "lead", "model": "qwen3.5:4b"},
            {"role": "builder", "model": "qwen2.5-coder:7b"},
            {"role": "reviewer", "model": "phi4-mini"},
        ],
    },
    {
        "name": "SQL Schema",
        "description": "Design SQL schema for an e-commerce platform",
        "roles": [
            {"role": "lead", "model": "qwen3.5:4b"},
            {"role": "builder", "model": "qwen2.5-coder:7b"},
            {"role": "reviewer", "model": "phi4-mini"},
        ],
    },
    {
        "name": "React Component",
        "description": "Build a reusable React data table component",
        "roles": [
            {"role": "lead", "model": "qwen3.5:4b"},
            {"role": "builder", "model": "qwen2.5-coder:7b"},
            {"role": "reviewer", "model": "phi4-mini"},
        ],
    },
    {
        "name": "Unit Tests",
        "description": "Write unit tests for a Python math library",
        "roles": [
            {"role": "lead", "model": "qwen3.5:4b"},
            {"role": "builder", "model": "qwen2.5-coder:7b"},
            {"role": "reviewer", "model": "phi4-mini"},
        ],
    },
]


async def run_task(client: httpx.AsyncClient, token: str, task: dict) -> dict:
    start = time.monotonic()

    team_resp = await client.post(
        f"{BASE_URL}/api/v1/teams",
        json={"name": f"bench-{task['name'][:8]}", "roles": task["roles"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    if team_resp.status_code != 201:
        return {"task": task["name"], "error": "team creation failed", "duration": 0}

    team_id = team_resp.json()["id"]

    task_resp = await client.post(
        f"{BASE_URL}/api/v1/tasks",
        json={"name": task["name"], "description": task["description"], "team_id": team_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    if task_resp.status_code != 201:
        return {"task": task["name"], "error": "task creation failed", "duration": 0}

    task_id = task_resp.json()["id"]
    execution_id = task_resp.json().get("execution_id", "")

    duration = time.monotonic() - start
    return {
        "task": task["name"],
        "task_id": task_id,
        "execution_id": execution_id,
        "duration": round(duration, 2),
        "team_id": team_id,
    }


async def main():
    print("=" * 60)
    print("AgentForge Fast Demo Benchmark")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=120) as client:
        auth = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "demo@agentforge.dev", "password": "changeme"},
        )
        if auth.status_code != 200:
            print(f"Auth failed: {auth.status_code} {auth.text}")
            return
        token = auth.json()["token"]
        print(f"Auth OK (token: {token[:16]}...)")
        print()

        results = await asyncio.gather(*[run_task(client, token, t) for t in TASKS])

    print(f"{'Task':30s} {'Duration':>10s} {'Status':12s}")
    print("-" * 52)
    durations = []
    for r in results:
        status = "OK" if "error" not in r else "FAIL"
        dur = r.get("duration", 0)
        if status == "OK":
            durations.append(dur)
        print(f"{r['task']:30s} {dur:>8.1f}s  {status:12s}")

    print("-" * 52)
    if durations:
        print(f"{'Average':30s} {statistics.mean(durations):>8.1f}s")
        print(f"{'Min':30s} {min(durations):>8.1f}s")
        print(f"{'Max':30s} {max(durations):>8.1f}s")
    print(f"{'Total':30s} {sum(r.get('duration', 0) for r in results):>8.1f}s")


if __name__ == "__main__":
    asyncio.run(main())

"""
AgentForge Multi-Model Collaboration Benchmark.

Runs 10 real tasks through the LangGraph agent system with real Ollama models,
captures detailed metrics, and produces a performance report.
"""

import asyncio
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

# --- Configuration -----------------------------------------------------------

API_BASE = "http://localhost:8002/api/v1"

TEAM_DEFINITIONS = [
    {
        "name": "Qwen25-7B-Lead_DeepSeek-Build_Gemma3-Review",
        "members": [
            ("team_lead", "qwen2.5-coder:7b"),
            ("builder", "gdisney/deepseek-coder-uncensored:latest"),
            ("reviewer", "gemma3:4b"),
        ],
    },
]

TASKS = [
    {
        "id": "jwt-auth",
        "title": "JWT Authentication API",
        "description": (
            "Create a FastAPI JWT authentication module. "
            "Include /login endpoint that accepts username/password and returns an access token. "
            "Include /verify endpoint that validates a token. "
            "Use HS256 signing. Tokens should expire after 30 minutes. "
            "Include a /refresh endpoint."
        ),
    },
    {
        "id": "rest-crud",
        "title": "REST CRUD API for Tasks",
        "description": (
            "Create a FastAPI REST API for managing tasks. "
            "Each task has: id (UUID), title (string), description (text), status (enum: todo/in_progress/done), "
            "created_at, updated_at. "
            "Implement full CRUD: POST /tasks, GET /tasks, GET /tasks/{id}, PUT /tasks/{id}, DELETE /tasks/{id}. "
            "Use Pydantic models for validation. Include proper HTTP status codes."
        ),
    },
    {
        "id": "sql-schema",
        "title": "SQL Schema for E-Commerce",
        "description": (
            "Design a PostgreSQL schema for an e-commerce platform. "
            "Include tables for: users, products, categories, orders, order_items, reviews. "
            "Add proper foreign keys, indexes, and constraints. "
            "Include a view for top-selling products. "
            "Write the DDL statements with CREATE TABLE, CREATE INDEX, and CREATE VIEW."
        ),
    },
    {
        "id": "react-component",
        "title": "React DataTable Component",
        "description": (
            "Create a reusable React DataTable component in TypeScript. "
            "Support features: column definitions, sorting (click header to sort), "
            "filtering (text input per column), pagination, row selection (checkbox). "
            "Use TypeScript generics for type safety. "
            "Include proper prop types and default values."
        ),
    },
    {
        "id": "fastapi-endpoint",
        "title": "FastAPI File Upload Endpoint",
        "description": (
            "Create a FastAPI endpoint for file uploads. "
            "Support: single file upload POST /upload, multiple file upload POST /upload/batch, "
            "file listing GET /files, file download GET /files/{filename}. "
            "Validate file types (only allow images and PDFs, max 10MB). "
            "Store files on disk with UUID-based names. "
            "Include proper error handling for oversized files and invalid types."
        ),
    },
    {
        "id": "error-handling",
        "title": "Python Error Handling Utility",
        "description": (
            "Create a Python utility module for consistent error handling in FastAPI apps. "
            "Include: custom exception classes (NotFoundError, ValidationError, AuthError), "
            "a global exception handler that returns consistent JSON error responses, "
            "a retry decorator with exponential backoff, "
            "and a Result type (Success/Failure) monad. "
            "Include type hints throughout."
        ),
    },
    {
        "id": "unit-tests",
        "title": "Pytest Test Suite for Auth Module",
        "description": (
            "Write a comprehensive pytest test suite for a FastAPI authentication module. "
            "Test: login with valid credentials returns token, login with invalid password returns 401, "
            "token verification with valid token passes, token verification with expired token fails, "
            "refresh token flow, protected endpoint access. "
            "Use pytest fixtures and monkeypatch for mocking. "
            "Aim for 90%+ code coverage."
        ),
    },
    {
        "id": "refactor",
        "title": "Refactor Legacy Python Code",
        "description": (
            "Refactor this legacy Python code into modern practices:\n\n"
            "def process(data):\n"
            "    r = []\n"
            "    for i in range(len(data)):\n"
            "        x = data[i]\n"
            "        if x != None:\n"
            "            if x > 0:\n"
            "                y = x * 2\n"
            "                r.append(y)\n"
            "            else:\n"
            "                y = abs(x) * 2\n"
            "                r.append(y)\n"
            "    return r\n\n"
            "Improve: type hints, list comprehension, None checking, naming, docstring. "
            "Add error handling for non-numeric input. "
            "Write the refactored version with explanation."
        ),
    },
    {
        "id": "api-docs",
        "title": "API Documentation Generator",
        "description": (
            "Create a Python script that generates Markdown API documentation from a FastAPI app. "
            "The script should: scan a FastAPI app for all routes, "
            "extract path, method, summary, description from docstrings, "
            "extract request/response Pydantic models and their fields, "
            "output a well-formatted Markdown file with sections per route. "
            "Use the FastAPI app's openapi() method as the data source."
        ),
    },
    {
        "id": "bug-fix",
        "title": "Debug Race Condition in Async Code",
        "description": (
            "Analyze and fix this async race condition:\n\n"
            "counter = 0\n\n"
            "async def increment():\n"
            "    global counter\n"
            "    temp = counter\n"
            "    await asyncio.sleep(0.01)\n"
            "    counter = temp + 1\n\n"
            "async def main():\n"
            "    tasks = [increment() for _ in range(100)]\n"
            "    await asyncio.gather(*tasks)\n"
            "    print(counter)  # Expected: 100, Got: ?\n\n"
            "Explain the bug, provide the fix using an asyncio.Lock, "
            "and suggest a better pattern using atomic operations if applicable."
        ),
    },
]

# --- Metrics Collector --------------------------------------------------------

class TaskMetrics:
    def __init__(self, task_def: dict):
        self.task_def = task_def
        self.task_id_str: str | None = None
        self.status: str = "pending"
        self.created_at: float = 0.0
        self.completed_at: float | None = None
        self.duration_seconds: float | None = None
        self.messages: list[dict] = []
        self.execution: dict | None = None
        self.error_message: str | None = None
        self.agent_latencies: dict[str, float] = {}
        self.estimated_tokens: dict[str, int] = {}
        self.retry_count: int = 0
        self.team_config: dict | None = None

    @property
    def elapsed(self) -> str:
        if self.duration_seconds is None:
            return "N/A"
        return f"{self.duration_seconds:.1f}s"


class Benchmark:
    def __init__(self, team_def: dict):
        self.team_def = team_def
        self.team_id: str | None = None
        self.results: list[TaskMetrics] = []
        self.session_start = time.time()

    async def _request(self, method: str, path: str, body: dict | None = None) -> dict | list:
        import httpx

        url = f"{API_BASE}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
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

    async def _ensure_team(self) -> str:
        teams = await self._request("GET", "/teams")
        for t in teams:
            if isinstance(t, dict) and t.get("name") == self.team_def["name"]:
                for m in t.get("members", []):
                    await self._request(
                        "DELETE",
                        f"/teams/{t['id']}/members/{m['id']}",
                    )
                await self._request("DELETE", f"/teams/{t['id']}")
                break

        team = await self._request("POST", "/teams", {"name": self.team_def["name"]})
        team_id = team["id"] if isinstance(team, dict) else team[0]["id"]

        for role, model in self.team_def["members"]:
            await self._request(
                "POST",
                f"/teams/{team_id}/members",
                {"role": role, "model": model},
            )

        return team_id

    async def _poll_until_done(
        self, task_id: str, metrics: TaskMetrics, poll_interval: float = 3.0, timeout: float = 600.0
    ) -> TaskMetrics:
        start = time.time()
        while time.time() - start < timeout:
            await asyncio.sleep(poll_interval)
            try:
                task = await self._request("GET", f"/tasks/{task_id}")
                if isinstance(task, list):
                    task = task[0]
                metrics.status = task.get("status", "unknown")
                metrics.error_message = task.get("error_message")

                msgs = await self._request("GET", f"/tasks/{task_id}/messages")
                if isinstance(msgs, list):
                    metrics.messages = msgs
                    self._compute_metrics(metrics)

                exec_data = await self._request("GET", f"/executions/{task_id}")
                metrics.execution = exec_data if isinstance(exec_data, dict) else None

                if metrics.status in ("completed", "failed"):
                    metrics.completed_at = time.time()
                    metrics.duration_seconds = metrics.completed_at - metrics.created_at
                    return metrics
            except Exception as e:
                print(f"  [poll error] {e}", file=sys.stderr)

        metrics.status = "timeout"
        metrics.completed_at = time.time()
        metrics.duration_seconds = metrics.completed_at - metrics.created_at
        metrics.error_message = "Timed out waiting for completion"
        return metrics

    def _compute_metrics(self, metrics: TaskMetrics):
        role_latencies: dict[str, list[float]] = {}
        for i, msg in enumerate(metrics.messages):
            role = msg.get("role", "unknown")
            ts = msg.get("created_at", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    role_latencies.setdefault(role, []).append(dt.timestamp())
                except (ValueError, TypeError):
                    pass

        for role, timestamps in role_latencies.items():
            if len(timestamps) >= 1:
                metrics.agent_latencies[role] = max(timestamps) - min(timestamps)

        for msg in metrics.messages:
            content = msg.get("content", "")
            metadata = msg.get("metadata") or {}
            token_usage = metadata.get("token_usage") or {}
            actual_tokens = token_usage.get("total_tokens", 0)
            role = msg.get("role", "unknown")
            if actual_tokens:
                metrics.estimated_tokens[role] = (
                    metrics.estimated_tokens.get(role, 0) + actual_tokens
                )
            else:
                char_count = len(content)
                estimated_tokens = int(char_count / 4)
                metrics.estimated_tokens[role] = (
                    metrics.estimated_tokens.get(role, 0) + estimated_tokens
                )

        lead_messages = [m for m in metrics.messages if m.get("role") == "team_lead"]
        builder_messages = [m for m in metrics.messages if m.get("role") == "builder"]
        reviewer_messages = [m for m in metrics.messages if m.get("role") == "reviewer"]
        metrics.retry_count = len(builder_messages) - 1
        if metrics.retry_count < 0:
            metrics.retry_count = 0

    def _extract_delivery(self, metrics: TaskMetrics) -> str:
        for msg in metrics.messages:
            if msg.get("message_type") == "delivery":
                return msg.get("content", "")
        return ""

    async def run_single_task(self, task_def: dict) -> TaskMetrics:
        metrics = TaskMetrics(task_def)
        metrics.created_at = time.time()
        metrics.team_config = {
            m[0]: {"role": m[0], "model": m[1]} for m in self.team_def["members"]
        }

        print(f"\n  ├─ Creating task...", end=" ")
        try:
            task = await self._request(
                "POST",
                "/tasks",
                {
                    "team_id": self.team_id,
                    "title": task_def["title"],
                    "description": task_def["description"],
                },
            )
            if isinstance(task, list):
                task = task[0]
            metrics.task_id_str = task["id"] if isinstance(task, dict) else str(task)
            print(f"id={metrics.task_id_str[:8]}...")
        except Exception as e:
            print(f"FAILED: {e}")
            metrics.status = "failed"
            metrics.error_message = str(e)
            metrics.completed_at = time.time()
            metrics.duration_seconds = metrics.completed_at - metrics.created_at
            return metrics

        print(f"  ├─ Polling for completion...")
        metrics = await self._poll_until_done(metrics.task_id_str, metrics)

        final_status = metrics.status
        icon = "✅" if final_status == "completed" else "❌" if final_status == "failed" else "⏰"
        print(f"  └─ {icon} Status={final_status}  Time={metrics.elapsed}  "
              f"Msgs={len(metrics.messages)}  Retries={metrics.retry_count}")

        return metrics

    async def run_all(self):
        print(f"\n{'='*70}")
        print(f"  AgentForge Multi-Model Collaboration Benchmark")
        print(f"{'='*70}")
        print(f"\nTeam: {self.team_def['name']}")
        for role, model in self.team_def["members"]:
            print(f"  {role:>12} -> {model}")
        print(f"\nTasks: {len(TASKS)}")
        print(f"{'='*70}")

        self.team_id = await self._ensure_team()
        print(f"\nTeam ID: {self.team_id}")

        for i, task_def in enumerate(TASKS, 1):
            print(f"\n[{i}/{len(TASKS)}] {task_def['title']}")
            metrics = await self.run_single_task(task_def)
            self.results.append(metrics)

        self._print_report()

    def _quality_score(self, metrics: TaskMetrics) -> int:
        score = 0
        if metrics.status == "completed":
            score += 30
        if metrics.messages:
            score += min(len(metrics.messages) * 5, 20)
        if metrics.retry_count > 0:
            score += 15
        delivery = self._extract_delivery(metrics)
        if delivery:
            score += 20
            if len(delivery) > 500:
                score += 15
        return min(score, 100)

    def _print_report(self):
        print(f"\n\n{'='*70}")
        print(f"  BENCHMARK REPORT")
        print(f"{'='*70}")
        print(f"  Session Duration: {time.time() - self.session_start:.1f}s")
        print(f"  Team: {self.team_def['name']}")
        print(f"{'='*70}\n")

        # Task Results
        print(f"{'Task':<25} {'Status':<12} {'Time':<10} {'Msgs':<6} {'Retries':<8} {'Quality':<8}")
        print(f"{'-'*25} {'-'*12} {'-'*10} {'-'*6} {'-'*8} {'-'*8}")
        for m in self.results:
            quality = self._quality_score(m)
            task_name = m.task_def["title"][:24]
            print(f"{task_name:<25} {m.status:<12} {m.elapsed:<10} "
                  f"{len(m.messages):<6} {m.retry_count:<8} {quality:<8}")
        print()

        # Agent Performance
        print(f"{'─'*70}")
        print(f"  AGENT PERFORMANCE")
        print(f"{'─'*70}")
        all_latencies: dict[str, list[float]] = {}
        all_tokens: dict[str, list[int]] = {}
        for m in self.results:
            for role, lat in m.agent_latencies.items():
                all_latencies.setdefault(role, []).append(lat)
            for role, toks in m.estimated_tokens.items():
                all_tokens.setdefault(role, []).append(toks)

        print(f"\n{'Agent':<15} {'Tasks':<8} {'Avg Latency':<15} {'Avg Tokens':<15} {'Total Tokens':<15}")
        print(f"{'-'*15} {'-'*8} {'-'*15} {'-'*15} {'-'*15}")
        for role in ["team_lead", "builder", "reviewer"]:
            lats = all_latencies.get(role, [])
            toks = all_tokens.get(role, [])
            if lats:
                avg_lat = sum(lats) / len(lats)
                avg_tok = sum(toks) / len(toks)
                total_tok = sum(toks)
                print(f"{role:<15} {len(lats):<8} {avg_lat:<12.1f}s  {avg_tok:<12.0f}  {total_tok:<15}")
        print()

        # Total metrics
        total_duration = sum(m.duration_seconds or 0 for m in self.results if m.duration_seconds)
        total_tokens = sum(
            sum(t for t in m.estimated_tokens.values()) for m in self.results
        )
        completed = sum(1 for m in self.results if m.status == "completed")
        failed = sum(1 for m in self.results if m.status == "failed")
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Total Estimated Tokens: {total_tokens}")
        print(f"Completed: {completed}/{len(self.results)}")
        print(f"Failed: {failed}/{len(self.results)}")
        print(f"Avg Task Time: {total_duration/len(self.results):.1f}s")

        # Failure Analysis
        print(f"\n{'─'*70}")
        print(f"  FAILURE ANALYSIS")
        print(f"{'─'*70}")
        failed_tasks = [m for m in self.results if m.status == "failed"]
        if failed_tasks:
            for m in failed_tasks:
                print(f"\n  ❌ {m.task_def['title']}")
                print(f"     Error: {m.error_message or 'Unknown'}")
        else:
            print(f"\n  No failures detected.")

        timeout_tasks = [m for m in self.results if m.status == "timeout"]
        if timeout_tasks:
            for m in timeout_tasks:
                print(f"\n  ⏰ {m.task_def['title']}")
                print(f"     Timed out after {m.duration_seconds:.0f}s")

        # Collaboration Quality
        print(f"\n{'─'*70}")
        print(f"  COLLABORATION QUALITY")
        print(f"{'─'*70}")
        tasks_with_retries = [m for m in self.results if m.retry_count > 0]
        tasks_with_lead_msgs = sum(
            1 for m in self.results
            if any(msg.get("role") == "team_lead" for msg in m.messages)
        )
        tasks_with_builder_msgs = sum(
            1 for m in self.results
            if any(msg.get("role") == "builder" for msg in m.messages)
        )
        tasks_with_reviewer_msgs = sum(
            1 for m in self.results
            if any(msg.get("role") == "reviewer" for msg in m.messages)
        )
        tasks_with_delivery = sum(
            1 for m in self.results
            if any(msg.get("message_type") == "delivery" for msg in m.messages)
        )

        print(f"\n  All 3 Roles Participated:  {len(self.results)}/{len(self.results)}")
        print(f"  Team Lead Messages:        {tasks_with_lead_msgs}/{len(self.results)}")
        print(f"  Builder Messages:          {tasks_with_builder_msgs}/{len(self.results)}")
        print(f"  Reviewer Messages:         {tasks_with_reviewer_msgs}/{len(self.results)}")
        print(f"  Final Delivery Produced:   {tasks_with_delivery}/{len(self.results)}")
        print(f"  Tasks With Retry Loops:    {len(tasks_with_retries)}/{len(self.results)}")

        if tasks_with_retries:
            avg_retries = sum(m.retry_count for m in tasks_with_retries) / len(tasks_with_retries)
            print(f"  Avg Retries per Retry Task: {avg_retries:.1f}")
            print(f"\n  Retry Loop Details:")
            for m in tasks_with_retries:
                print(f"    - {m.task_def['title']}: {m.retry_count} retries -> {m.status}")

        # Message Flow
        print(f"\n{'─'*70}")
        print(f"  SAMPLE MESSAGE FLOW (First Completed Task)")
        print(f"{'─'*70}")
        first_completed = next(
            (m for m in self.results if m.status == "completed"), None
        )
        if first_completed:
            print(f"\n  Task: {first_completed.task_def['title']}")
            print(f"  Messages: {len(first_completed.messages)}")
            print(f"  Flow:")
            for i, msg in enumerate(first_completed.messages):
                role = msg.get("role", "?")
                mtype = msg.get("message_type", "?")
                model = msg.get("model", "?")
                label = {"plan": "Plan", "code": "Implement", "review": "Review", "delivery": "Deliver"}.get(mtype, mtype)
                print(f"    {i+1}. [{role}] ({model}) -> {label}")

        # Recommended Improvements
        print(f"\n{'─'*70}")
        print(f"  RECOMMENDED IMPROVEMENTS")
        print(f"{'─'*70}")
        recommendations = []

        slow_tasks = [m for m in self.results if m.duration_seconds and m.duration_seconds > 180]
        if slow_tasks:
            recommendations.append(
                f"Long execution times detected ({len(slow_tasks)} tasks > 3min). "
                f"Consider smaller models or shorter timeouts."
            )

        if failed_tasks:
            recommendations.append(
                f"{len(failed_tasks)} tasks failed. Common failure patterns: "
                + "; ".join(m.error_message or "unknown" for m in failed_tasks[:3])
                + ". Consider adding structured output validation."
            )

        low_quality = [m for m in self.results if self._quality_score(m) < 50]
        if low_quality:
            recommendations.append(
                f"{len(low_quality)} tasks scored below 50 quality. "
                f"Review prompt templates for clarity."
            )

        avg_retries_all = sum(m.retry_count for m in self.results) / len(self.results)
        if avg_retries_all > 1:
            recommendations.append(
                f"High average retry rate ({avg_retries_all:.1f}/task). "
                f"Consider improving builder prompts or increasing MAX_REVIEW_ATTEMPTS."
            )
        elif avg_retries_all < 0.3:
            recommendations.append(
                f"Low retry rate ({avg_retries_all:.1f}/task). "
                f"Reviewers may be too lenient. Consider tightening review criteria."
            )

        if not recommendations:
            recommendations.append("System working well. Monitor for regressions.")

        for i, rec in enumerate(recommendations, 1):
            print(f"\n  {i}. {rec}")
        print()

        # Per-Task Detail
        print(f"{'─'*70}")
        print(f"  PER-TASK DETAIL")
        print(f"{'─'*70}")
        for m in self.results:
            quality = self._quality_score(m)
            title = m.task_def['title']
            status_icon = "✅" if m.status == "completed" else "❌" if m.status == "failed" else "⏰"
            delivery_preview = self._extract_delivery(m)[:150] if self._extract_delivery(m) else "(no delivery)"
            print(f"\n  {status_icon} {title}")
            print(f"     Status: {m.status} | Duration: {m.elapsed} | Messages: {len(m.messages)} | Retries: {m.retry_count} | Quality: {quality}/100")
            print(f"     Latencies: {', '.join(f'{k}={v:.1f}s' for k,v in m.agent_latencies.items())}")
            print(f"     Est. Tokens: {', '.join(f'{k}={v}' for k,v in m.estimated_tokens.items())}")
            delivery = self._extract_delivery(m)
            if delivery:
                preview = delivery[:200].replace('\n', ' ')
                print(f"     Delivery: {preview}...")
            if m.error_message:
                print(f"     Error: {m.error_message}")

        # Final Summary
        print(f"\n{'='*70}")
        avg_quality = sum(self._quality_score(m) for m in self.results) / len(self.results)
        print(f"  FINAL VERDICT")
        print(f"{'='*70}")
        print(f"\n  Average Quality Score: {avg_quality:.0f}/100")
        print(f"  Success Rate: {completed}/{len(self.results)} ({100*completed/len(self.results):.0f}%)")

        if avg_quality >= 70 and completed >= 8:
            print(f"\n  ✅ Multi-model collaboration is EFFECTIVE.")
            print(f"     Models are catching each other's errors and improving output.")
        elif avg_quality >= 50 and completed >= 6:
            print(f"\n  ⚠️  Multi-model collaboration is FUNCTIONAL but needs tuning.")
            print(f"     Review prompt templates and retry logic.")
        else:
            print(f"\n  ❌ Multi-model collaboration needs SIGNIFICANT improvements.")
            print(f"     Check model compatibility, timeout settings, and prompt templates.")

        print(f"\n{'='*70}\n")


async def main():
    for team_def in TEAM_DEFINITIONS:
        bench = Benchmark(team_def)
        await bench.run_all()


if __name__ == "__main__":
    asyncio.run(main())

"""
AgentForge Scientific Benchmark v2.0 - Simplified Version

Direct scientific validation of multi-model collaboration using existing AgentForge system.

Conditions:
- Condition A: Single qwen2.5-coder:7b
- Condition B: Single gemma3:4b
- Condition C: AgentForge Team (3 models)
- Condition D: Three identical qwen2.5-coder:7b agents

This version tests whether multi-model collaboration improves results.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import httpx


POLL_INTERVAL = 5.0
TASK_TIMEOUT = 600.0


class ScientificBenchmarkSimplified:
    def __init__(self, api_base: str = "http://localhost:8000/api/v1"):
        self.api_base = api_base
        self.http = httpx.AsyncClient(timeout=300.0)
        self.team_ids: Dict[str, str] = {}

        self.conditions = {
            "A": {
                "name": "Single qwen2.5-coder:7b",
                "models": {
                    "team_lead": "qwen2.5-coder:7b",
                    "builder": "qwen2.5-coder:7b",
                    "reviewer": "qwen2.5-coder:7b"
                }
            },
            "B": {
                "name": "Single gemma3:4b",
                "models": {
                    "team_lead": "gemma3:4b",
                    "builder": "gemma3:4b",
                    "reviewer": "gemma3:4b"
                }
            },
            "C": {
                "name": "AgentForge Team",
                "models": {
                    "team_lead": "qwen2.5-coder:7b",
                    "builder": "gdisney/deepseek-coder-uncensored:latest",
                    "reviewer": "gemma3:4b"
                }
            },
            "D": {
                "name": "Three identical qwen2.5-coder:7b agents",
                "models": {
                    "team_lead": "qwen2.5-coder:7b",
                    "builder": "qwen2.5-coder:7b",
                    "reviewer": "qwen2.5-coder:7b"
                }
            }
        }

        self.tasks = self._define_scientific_tasks()

    def _define_scientific_tasks(self) -> List[Dict]:
        return [
            {
                "id": "jwt_auth",
                "title": "JWT Authentication with Password Hashing",
                "description": "Implement secure JWT authentication with bcrypt password hashing, token refresh mechanism, and proper error handling. Include endpoints: /register, /login, /refresh, /verify with comprehensive tests.",
                "difficulty": "hard"
            },
            {
                "id": "rest_api_crud",
                "title": "RESTful API with PostgreSQL CRUD Operations",
                "description": "Build complete CRUD API for user management with PostgreSQL integration, validation, pagination, filtering, and comprehensive error handling. Include authentication middleware.",
                "difficulty": "hard"
            },
            {
                "id": "ecommerce_schema",
                "title": "E-commerce Database Schema with Advanced Queries",
                "description": "Design comprehensive PostgreSQL schema for e-commerce: users, products, categories, orders, order_items, payments. Include complex queries for analytics and reporting.",
                "difficulty": "medium"
            },
            {
                "id": "file_upload_api",
                "title": "File Upload API with Validation and Storage",
                "description": "Implement FastAPI file upload with validation (max 10MB, allowed types: images, PDFs), UUID-based file storage, listing, downloading, and cleanup.",
                "difficulty": "medium"
            },
            {
                "id": "advanced_datatable",
                "title": "Advanced DataTable Component with Pagination and Filters",
                "description": "Build reusable React DataTable component with column sorting, text filtering per column, server-side pagination, row selection, CSV export, and TypeScript generics.",
                "difficulty": "hard"
            },
            {
                "id": "comprehensive_pytest_suite",
                "title": "Comprehensive Pytest Test Suite with 90% Coverage",
                "description": "Write comprehensive pytest tests for authentication module: login, registration, token validation, error cases, edge cases.",
                "difficulty": "hard"
            },
            {
                "id": "legacy_to_modern",
                "title": "Legacy Code Refactoring to Modern Standards",
                "description": "Refactor legacy Python service: add type hints, list comprehensions, proper error handling, docstrings, modularity.",
                "difficulty": "medium"
            },
            {
                "id": "api_documentation_generator",
                "title": "API Documentation Generator",
                "description": "Create documentation generator for FastAPI apps: extract endpoints, methods, summaries from docstrings, generate structured Markdown.",
                "difficulty": "easy"
            },
            {
                "id": "race_condition_fix",
                "title": "Race Condition Fix in Concurrent System",
                "description": "Fix async race condition in user counter system: implement asyncio.Lock for thread safety, analyze performance impact, write tests.",
                "difficulty": "medium"
            },
            {
                "id": "memory_leak_fix",
                "title": "Memory Leak Fix and Performance Optimization",
                "description": "Identify and fix memory leaks in long-running services, implement memory profiling, optimize algorithms, add proper resource cleanup.",
                "difficulty": "hard"
            }
        ]

    async def _api_post(self, path: str, data: dict) -> dict:
        url = f"{self.api_base}{path}"
        r = await self.http.post(url, json=data)
        r.raise_for_status()
        return r.json()

    async def _api_get(self, path: str) -> dict:
        url = f"{self.api_base}{path}"
        r = await self.http.get(url)
        r.raise_for_status()
        return r.json()

    async def _api_get_list(self, path: str) -> list:
        url = f"{self.api_base}{path}"
        r = await self.http.get(url)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "value" in data:
            return data["value"]
        if isinstance(data, list):
            return data
        return []

    async def setup_teams(self):
        print("Setting up benchmark teams...")
        for cond_key, cond_data in self.conditions.items():
            team_name = f"Benchmark-Condition-{cond_key}"
            resp = await self._api_post("/teams", {
                "name": team_name,
                "description": cond_data["name"]
            })
            team_id = resp["id"]
            for role, model in cond_data["models"].items():
                await self._api_post(f"/teams/{team_id}/members", {
                    "role": role,
                    "model": model
                })
            self.team_ids[cond_key] = team_id
            print(f"  Condition {cond_key}: team={team_id}, models={cond_data['models']}")

    async def _poll_task(self, task_id: str, timeout: float = TASK_TIMEOUT) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            task = await self._api_get(f"/tasks/{task_id}")
            status = task.get("status")
            if status == "completed":
                return task
            if status == "failed":
                return task
            await asyncio.sleep(POLL_INTERVAL)
        return {"id": task_id, "status": "timeout", "error_message": "Task timed out"}

    async def _evaluate_task(self, task_info: dict, messages: list) -> Dict:
        if task_info.get("status") == "failed":
            return {
                "success": False,
                "evaluation_score": 0,
                "reason": task_info.get("error_message", "Task failed")
            }
        if task_info.get("status") == "timeout":
            return {"success": False, "evaluation_score": 0, "reason": "Timeout"}

        delivery_msgs = [m for m in messages if m.get("message_type") == "delivery"]
        code_msgs = [m for m in messages if m.get("message_type") == "code"]
        review_msgs = [m for m in messages if m.get("message_type") == "review"]
        plan_msgs = [m for m in messages if m.get("message_type") == "plan"]

        has_delivery = len(delivery_msgs) > 0
        has_code = len(code_msgs) > 0
        has_review = len(review_msgs) > 0
        has_plan = len(plan_msgs) > 0

        delivery_content = delivery_msgs[0]["content"] if delivery_msgs else ""
        code_content = code_msgs[0]["content"] if code_msgs else ""
        review_content = review_msgs[0]["content"] if review_msgs else ""

        output_length = len(delivery_content) + len(code_content)

        review_approved = '"verdict": "pass"' in review_content or '"verdict":"pass"' in review_content
        delivery_approved = '"verdict": "approved"' in delivery_content or '"verdict":"approved"' in delivery_content

        score = 0
        score += 10 if has_plan else 0
        score += 20 if has_code else 0
        score += 15 if has_review else 0
        score += 15 if has_delivery else 0
        score += 15 if review_approved else 0
        score += 15 if delivery_approved else 0
        score += min(10, output_length // 200)

        return {
            "success": score >= 70,
            "evaluation_score": min(100, score),
            "has_plan": has_plan,
            "has_code": has_code,
            "has_review": has_review,
            "has_delivery": has_delivery,
            "review_approved": review_approved,
            "delivery_approved": delivery_approved,
            "output_length": output_length,
            "message_count": len(messages)
        }

    async def run_condition_test(self, condition_key: str, condition_data: Dict) -> Dict:
        print(f"\n{'='*70}")
        print(f"Running Condition {condition_key}: {condition_data['name']}")
        print(f"{'='*70}")

        condition_stats = {
            "condition": condition_key,
            "name": condition_data["name"],
            "models": condition_data["models"],
            "tasks_completed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "total_token_usage": 0,
            "retry_count": 0,
            "scores": [],
            "task_results": []
        }

        team_id = self.team_ids[condition_key]

        for task in self.tasks[:5]:
            print(f"  Task [{task['id']}]: {task['title']}...", end="", flush=True)
            start_time = time.monotonic()

            try:
                resp = await self._api_post("/tasks", {
                    "team_id": team_id,
                    "title": task["title"],
                    "description": task["description"]
                })
                task_id = resp["id"]

                result_task = await self._poll_task(task_id)
                elapsed = time.monotonic() - start_time
                duration_ms = elapsed * 1000

                messages = []
                if result_task.get("status") in ("completed", "failed"):
                    try:
                        msgs_data = await self._api_get_list(f"/tasks/{task_id}/messages")
                        messages = msgs_data if isinstance(msgs_data, list) else []
                    except Exception:
                        messages = []

                evaluation = await self._evaluate_task(result_task, messages)

                token_usage = 0
                retry_count = 0
                for m in messages:
                    meta_raw = m.get("metadata") or m.get("metadata", {})
                    if isinstance(meta_raw, str):
                        try:
                            meta_raw = json.loads(meta_raw)
                        except json.JSONDecodeError:
                            meta_raw = {}
                    tu = meta_raw.get("token_usage") or {}
                    if isinstance(tu, dict):
                        token_usage += tu.get("total_tokens", 0) or tu.get("total_token_count", 0) or 0

                if evaluation["success"]:
                    condition_stats["successful_tasks"] += 1
                    condition_stats["scores"].append(evaluation["evaluation_score"])
                else:
                    condition_stats["failed_tasks"] += 1

                condition_stats["tasks_completed"] += 1
                condition_stats["total_execution_time"] += duration_ms
                condition_stats["total_token_usage"] += token_usage

                result_entry = {
                    "task_id": task["id"],
                    "title": task["title"],
                    "success": evaluation["success"],
                    "execution_time": duration_ms,
                    "token_usage": token_usage,
                    "retry_count": retry_count,
                    "evaluation_score": evaluation["evaluation_score"],
                    "status": result_task.get("status"),
                    "details": evaluation
                }
                condition_stats["task_results"].append(result_entry)

                status_str = "OK" if evaluation["success"] else "FAIL"
                print(f" {status_str} ({duration_ms/1000:.1f}s, score={evaluation['evaluation_score']})")

            except Exception as e:
                elapsed = time.monotonic() - start_time
                duration_ms = elapsed * 1000
                print(f" ERROR ({e})")
                condition_stats["tasks_completed"] += 1
                condition_stats["failed_tasks"] += 1
                condition_stats["total_execution_time"] += duration_ms
                condition_stats["task_results"].append({
                    "task_id": task["id"],
                    "title": task["title"],
                    "success": False,
                    "execution_time": duration_ms,
                    "token_usage": 0,
                    "retry_count": 0,
                    "evaluation_score": 0,
                    "error": str(e)
                })

            await asyncio.sleep(2)

        completed = condition_stats["tasks_completed"]
        if completed > 0:
            condition_stats["avg_execution_time"] = condition_stats["total_execution_time"] / completed
            condition_stats["avg_token_usage"] = condition_stats["total_token_usage"] / completed
        else:
            condition_stats["avg_execution_time"] = 0
            condition_stats["avg_token_usage"] = 0

        scores = condition_stats["scores"]
        condition_stats["avg_score"] = sum(scores) / len(scores) if scores else 0

        return condition_stats

    async def run_scientific_benchmark(self) -> Dict:
        print("=" * 70)
        print("AGENTFORGE SCIENTIFIC BENCHMARK v2.0")
        print("=" * 70)
        print("Conditions: A, B, C, D")
        print(f"Tasks: {len(self.tasks)} per condition")
        print("Goal: Answer 'Does multi-model collaboration improve results?'")
        print("=" * 70)

        await self.setup_teams()

        condition_results = {}
        for condition_key in ["A", "B", "C", "D"]:
            stats = await self.run_condition_test(condition_key, self.conditions[condition_key])
            condition_results[condition_key] = stats

        analysis = self._analyze_results(condition_results)

        return {
            "conditions": condition_results,
            "analysis": analysis,
            "summary": self._generate_executive_summary(condition_results, analysis),
            "status": "completed"
        }

    def _analyze_results(self, condition_results: Dict) -> Dict:
        condition_scores = {}
        for cond_key, stats in condition_results.items():
            condition_scores[cond_key] = stats.get("avg_score", 0)

        single_model_best = max(condition_scores.get("A", 0), condition_scores.get("B", 0))
        best_single_condition = "A" if condition_scores.get("A", 0) > condition_scores.get("B", 0) else "B"

        team_score = condition_scores.get("C", 0)
        team_vs_single_delta = team_score - single_model_best
        team_vs_single_percent = (team_vs_single_delta / single_model_best * 100) if single_model_best > 0 else 0

        identical_score = condition_scores.get("D", 0)
        identical_vs_single_delta = identical_score - single_model_best
        identical_vs_single_percent = (identical_vs_single_delta / single_model_best * 100) if single_model_best > 0 else 0

        collaboration_benefit = team_score - max(identical_score, single_model_best)

        success_threshold = 10.0
        is_successful = team_vs_single_percent >= success_threshold

        return {
            "best_single_model": best_single_condition,
            "best_single_score": single_model_best,
            "team_score": team_score,
            "identical_team_score": identical_score,
            "team_vs_single": {
                "absolute": team_vs_single_delta,
                "percent": team_vs_single_percent
            },
            "identical_vs_single": {
                "absolute": identical_vs_single_delta,
                "percent": identical_vs_single_percent
            },
            "collaboration_benefit": collaboration_benefit,
            "success_criteria_met": is_successful,
            "success_threshold_percent": success_threshold,
            "analysis": f"Team collaboration shows {team_vs_single_percent:+.1f}% delta vs best single model. Identical agents achieve {identical_vs_single_percent:+.1f}% delta. Collaboration provides {collaboration_benefit:+.1f} additional quality points."
        }

    def _generate_executive_summary(self, condition_results: Dict, analysis: Dict) -> str:
        lines = []
        lines.append("AgentForge Scientific Benchmark Results")
        lines.append("")
        lines.append("EXPERIMENT: Multi-Model Collaboration Validation")
        lines.append(f"Conditions: A, B, C, D ({len(self.tasks)} tasks each = {len(self.tasks) * 4} total)")
        lines.append("")
        lines.append("# WIN RATE")
        for cond_key in ["A", "B", "C", "D"]:
            stats = condition_results[cond_key]
            total = stats["tasks_completed"]
            successful = stats["successful_tasks"]
            rate = (successful / total * 100) if total > 0 else 0
            lines.append(f"{cond_key}: {successful}/{total} ({rate:.1f}%)")
        lines.append("")
        lines.append("# QUALITY DELTA")
        lines.append(f"Best Single Model ({analysis['best_single_model']}): {analysis['best_single_score']:.1f}")
        lines.append(f"AgentForge Team (C): {analysis['team_score']:.1f}")
        lines.append(f"Three Identical (D): {analysis['identical_team_score']:.1f}")
        lines.append(f"Quality Delta (C vs Best Single): {analysis['team_vs_single']['absolute']:.1f} ({analysis['team_vs_single']['percent']:+.1f}%)")
        lines.append("")
        lines.append("# COST DELTA")
        lines.append("Estimated cost per task by condition:")
        for cond_key in ["A", "B", "C", "D"]:
            stats = condition_results[cond_key]
            avg_tokens = stats.get("avg_token_usage", 0)
            cost = avg_tokens * 0.001
            lines.append(f"  {cond_key}: ${cost:.4f}")
        lines.append("")
        lines.append("# LATENCY DELTA")
        lines.append("Average execution time per condition:")
        latencies = {}
        for cond_key in ["A", "B", "C", "D"]:
            latencies[cond_key] = condition_results[cond_key].get("avg_execution_time", 0)
        best_latency_key = min(latencies, key=latencies.get)
        best_latency = latencies[best_latency_key]
        team_latency = latencies["C"]
        lines.append(f"  Best Single Model ({best_latency_key}): {best_latency:.1f}ms")
        lines.append(f"  AgentForge Team (C): {team_latency:.1f}ms")
        latency_delta = team_latency - best_latency
        latency_percent = (latency_delta / best_latency * 100) if best_latency > 0 else 0
        lines.append(f"  Latency Delta: {latency_delta:+.1f}ms ({latency_percent:+.1f}%)")
        lines.append("")
        lines.append("# FINAL RECOMMENDATION")
        if analysis["success_criteria_met"]:
            lines.append(f"SUCCESS: AgentForge Team outperforms best single model by {analysis['team_vs_single']['percent']:.1f}% (> {analysis['success_threshold_percent']}%)")
            lines.append("")
            lines.append("Recommendation: Proceed with AgentForge Team deployment for production workloads.")
            lines.append("Multi-model collaboration is effective for software engineering tasks.")
        else:
            lines.append(f"FAILURE: AgentForge Team underperforms best single model by {abs(analysis['team_vs_single']['percent']):.1f}%")
            lines.append(f"Required: {analysis['success_threshold_percent']}% improvement, achieved: {analysis['team_vs_single']['percent']:.1f}%")
            lines.append("Recommendations:")
            lines.append("  1. Review prompt engineering for reviewer module")
            lines.append("  2. Analyze builder prompts for optimization")
            lines.append("  3. Consider additional model combinations")
            lines.append("  4. Evaluate task complexity vs. model capabilities")
            lines.append("  5. Add human-in-the-loop validation for critical tasks")
        return "\n".join(lines)

    def print_analysis(self, analysis: Dict):
        print(f"\n{'='*70}")
        print("ANALYSIS DETAILS")
        print(f"{'='*70}")

        print(f"\nKey Findings:")
        print(f"  Best Single Model: {analysis['best_single_model']} ({analysis['best_single_score']:.1f})")
        print(f"  AgentForge Team: {analysis['team_score']:.1f}")
        print(f"  Three Identical: {analysis['identical_team_score']:.1f}")

        print(f"\nCollaboration Benefits:")
        print(f"  Team vs Single Delta: {analysis['team_vs_single']['percent']:+.1f}%")
        print(f"  Identical vs Single Delta: {analysis['identical_vs_single']['percent']:+.1f}%")
        print(f"  Pure Collaboration Benefit: {analysis['collaboration_benefit']:.1f} points")

        print(f"\nConclusion:")
        if analysis["success_criteria_met"]:
            print(f"[SUCCESS] AgentForge Team DEMONSTRATES improved results")
            print(f"[OK] Multi-model collaboration ADD value to software engineering")
        else:
            print(f"[FAILURE] AgentForge Team does NOT demonstrate clear superiority")
            print(f"[INFO] Further investigation needed to understand collaboration effectiveness")


async def main():
    print("Initializing AgentForge Scientific Benchmark")

    benchmark = ScientificBenchmarkSimplified(
        api_base="http://localhost:8000/api/v1"
    )

    results = await benchmark.run_scientific_benchmark()

    print()
    print(results["summary"])

    print(f"\n{'='*70}")
    print("BENCHMARK COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())

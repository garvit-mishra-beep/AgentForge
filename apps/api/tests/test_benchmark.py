"""Tests for the benchmark scorer and runner (offline, deterministic)."""

import pytest

from benchmarks.runner import MockSolver, run_benchmark
from benchmarks.scorer import extract_code, load_dataset, score_output


def test_dataset_loads_and_is_wellformed():
    tasks = load_dataset()
    assert len(tasks) >= 5
    for t in tasks:
        assert "id" in t and "prompt" in t and "rubric" in t


def test_extract_code_from_fence():
    out = "Here you go:\n```python\ndef f():\n    return 1\n```\nDone."
    assert "def f():" in extract_code(out)


def test_extract_code_from_builder_json():
    out = '{"summary": "x", "files": [{"path": "a.py", "content": "def g():\\n    return 2"}]}'
    assert "def g():" in extract_code(out)


def test_reference_solution_passes_and_bug_fails():
    tasks = {t["id"]: t for t in load_dataset()}
    good = "```python\ndef is_prime(n):\n    if n<2: return False\n    i=2\n    while i*i<=n:\n        if n%i==0: return False\n        i+=1\n    return True\n```"
    bad = "```python\ndef is_prime(n):\n    return n%2==1\n```"  # 9 -> True (wrong)
    assert score_output(tasks["py-isprime"], good).passed
    assert not score_output(tasks["py-isprime"], bad).passed


def test_forbidden_substring_is_penalized():
    tasks = {t["id"]: t for t in load_dataset()}
    injected = "```python\ndef build_user_query(user_id):\n    return (f\"SELECT * FROM users WHERE id = {user_id}\", ())\n```"
    res = score_output(tasks["py-safe-sql"], injected)
    forbidden_check = next(c for c in res.checks if c.name == "forbidden")
    assert not forbidden_check.passed


@pytest.mark.asyncio
async def test_run_benchmark_computes_real_lift():
    """Mock 'good' solver must measurably beat mock 'buggy' on computed metrics."""
    report = await run_benchmark([MockSolver("buggy"), MockSolver("good")])
    conds = {c["name"]: c for c in report["conditions"]}
    assert conds["mock:buggy"]["pass_rate"] < conds["mock:good"]["pass_rate"]
    assert conds["mock:good"]["pass_rate"] == 1.0
    # Delta is computed, not hardcoded.
    cmp = report["comparisons"][0]
    assert cmp["pass_rate_delta"] > 0

"""Benchmark runner: compare conditions on the labeled dataset and compute deltas.

A *condition* is a way of solving a task, expressed as a ``Solver``. We ship:

  - ``SingleModelSolver``    — one model, one shot (the baseline).
  - ``TeamReviewSolver``     — builder -> reviewer -> builder repair loop. This is
                               the multi-agent hypothesis: does a review+repair
                               loop beat a single pass?
  - ``MockSolver``           — deterministic, no network. Lets the harness + its
                               numbers be unit-tested in CI without Ollama.

The runner scores every (condition, task) pair with :mod:`benchmarks.scorer`,
aggregates pass-rate / mean-score per condition, and reports the *computed* lift
of the team over the baseline — replacing the fictional hardcoded "40%".
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from benchmarks.scorer import ScoreResult, load_dataset, score_output


class Solver(Protocol):
    name: str

    async def solve(self, task: dict) -> str:
        ...


# ── Real solvers (require a live provider, e.g. Ollama) ────────────────────


@dataclass
class SingleModelSolver:
    model: str
    name: str = ""

    def __post_init__(self):
        self.name = self.name or f"single:{self.model}"

    async def solve(self, task: dict) -> str:
        from core.providers import get_provider

        provider = get_provider(self.model)
        system = (
            "You are an expert programmer. Output ONLY a single fenced code block "
            "containing the complete solution. No prose."
        )
        resp = await provider.chat(self.model, system, task["prompt"], max_tokens=1024)
        return resp.content


@dataclass
class TeamReviewSolver:
    """Builder -> reviewer -> builder-repair. The multi-agent condition."""

    builder_model: str
    reviewer_model: str
    name: str = "team:review+repair"

    async def solve(self, task: dict) -> str:
        from core.providers import get_provider

        builder = get_provider(self.builder_model)
        reviewer = get_provider(self.reviewer_model)

        build_sys = (
            "You are an expert programmer. Output ONLY a single fenced code block "
            "with the complete solution. No prose."
        )
        first = (await builder.chat(self.builder_model, build_sys, task["prompt"], max_tokens=1024)).content

        review_sys = (
            "You are a meticulous code reviewer. Given a task and a candidate "
            "solution, list concrete bugs or missing edge cases as terse bullet "
            "points. If perfect, reply exactly 'LGTM'."
        )
        review = (await reviewer.chat(
            self.reviewer_model, review_sys,
            f"TASK:\n{task['prompt']}\n\nSOLUTION:\n{first}", max_tokens=512,
        )).content

        if "lgtm" in review.lower() and len(review.strip()) < 12:
            return first

        repair_sys = (
            "You are an expert programmer. Apply the reviewer's feedback and output "
            "ONLY a single fenced code block with the corrected complete solution."
        )
        repaired = (await builder.chat(
            self.builder_model, repair_sys,
            f"TASK:\n{task['prompt']}\n\nYOUR DRAFT:\n{first}\n\nREVIEW FEEDBACK:\n{review}",
            max_tokens=1024,
        )).content
        return repaired


# ── Mock solver (deterministic, for CI) ────────────────────────────────────


class MockSolver:
    """Returns canned solutions so the harness is testable offline.

    ``quality`` controls behavior: ``"good"`` returns reference solutions for all
    tasks; ``"buggy"`` returns subtly wrong code (off-by-one / wrong base cases)
    so the two conditions produce *different, computed* scores.
    """

    _GOOD = {
        "py-fib": "```python\ndef fib(n):\n    a,b=0,1\n    for _ in range(n): a,b=b,a+b\n    return a\n```",
        "py-isprime": "```python\ndef is_prime(n):\n    if n<2: return False\n    i=2\n    while i*i<=n:\n        if n%i==0: return False\n        i+=1\n    return True\n```",
        "py-reverse": "```python\ndef reverse_words(s):\n    return ' '.join(reversed(s.split()))\n```",
        "py-anagram": "```python\ndef is_anagram(a,b):\n    f=lambda s: sorted(s.replace(' ','').lower())\n    return f(a)==f(b)\n```",
        "py-safe-sql": "```python\ndef build_user_query(user_id):\n    return ('SELECT * FROM users WHERE id = $1', (user_id,))\n```",
        "py-fizzbuzz": "```python\ndef fizzbuzz(n):\n    out=[]\n    for i in range(1,n+1):\n        if i%15==0: out.append('FizzBuzz')\n        elif i%3==0: out.append('Fizz')\n        elif i%5==0: out.append('Buzz')\n        else: out.append(str(i))\n    return out\n```",
    }
    _BUGGY = {
        # off-by-one: returns fib(n+1)
        "py-fib": "```python\ndef fib(n):\n    a,b=0,1\n    for _ in range(n): a,b=b,a+b\n    return b\n```",
        # treats 1 as prime
        "py-isprime": "```python\ndef is_prime(n):\n    if n<1: return False\n    i=2\n    while i<n:\n        if n%i==0: return False\n        i+=1\n    return True\n```",
        # doesn't collapse multiple spaces
        "py-reverse": "```python\ndef reverse_words(s):\n    return ' '.join(s.split(' ')[::-1])\n```",
        "py-anagram": "```python\ndef is_anagram(a,b):\n    return sorted(a)==sorted(b)\n```",
        # SQL injection via f-string
        "py-safe-sql": "```python\ndef build_user_query(user_id):\n    return (f\"SELECT * FROM users WHERE id = {user_id}\", ())\n```",
        # wrong: 15 -> only Fizz
        "py-fizzbuzz": "```python\ndef fizzbuzz(n):\n    out=[]\n    for i in range(1,n+1):\n        if i%3==0: out.append('Fizz')\n        elif i%5==0: out.append('Buzz')\n        else: out.append(str(i))\n    return out\n```",
    }

    def __init__(self, quality: str = "good", name: str | None = None):
        self.quality = quality
        self.name = name or f"mock:{quality}"

    async def solve(self, task: dict) -> str:
        table = self._GOOD if self.quality == "good" else self._BUGGY
        return table.get(task["id"], "```python\n# no solution\n```")


# ── Aggregation ────────────────────────────────────────────────────────────


@dataclass
class ConditionResult:
    name: str
    results: list[ScoreResult]

    @property
    def pass_rate(self) -> float:
        return sum(1 for r in self.results if r.passed) / len(self.results) if self.results else 0.0

    @property
    def mean_score(self) -> float:
        return sum(r.score for r in self.results) / len(self.results) if self.results else 0.0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "pass_rate": round(self.pass_rate, 4),
            "mean_score": round(self.mean_score, 4),
            "n": len(self.results),
            "results": [r.as_dict() for r in self.results],
        }


async def run_condition(
    solver: Solver, tasks: list[dict], run_tests: bool = True,
    concurrency: int = 4,
) -> ConditionResult:
    sem = asyncio.Semaphore(concurrency)

    async def _one(task: dict) -> ScoreResult:
        async with sem:
            try:
                output = await solver.solve(task)
            except Exception as e:  # a provider error shouldn't abort the run
                output = f"# solver error: {e}"
            return score_output(task, output, run_tests=run_tests)

    results = await asyncio.gather(*[_one(t) for t in tasks])
    return ConditionResult(solver.name, list(results))


async def run_benchmark(
    solvers: list[Solver], dataset_path=None, run_tests: bool = True,
) -> dict:
    """Run all solvers over the dataset and compute lift vs the first condition."""
    tasks = load_dataset(dataset_path)
    conditions = [await run_condition(s, tasks, run_tests=run_tests) for s in solvers]

    baseline = conditions[0]
    comparisons = []
    for cond in conditions[1:]:
        # Relative lift is undefined when the baseline never passes; report it as
        # null rather than a misleading division-by-near-zero blow-up.
        lift = (
            round((cond.pass_rate - baseline.pass_rate) / baseline.pass_rate * 100, 1)
            if baseline.pass_rate > 0
            else None
        )
        comparisons.append({
            "condition": cond.name,
            "vs": baseline.name,
            "pass_rate_delta": round(cond.pass_rate - baseline.pass_rate, 4),
            "pass_rate_lift_pct": lift,
            "mean_score_delta": round(cond.mean_score - baseline.mean_score, 4),
        })

    return {
        "n_tasks": len(tasks),
        "conditions": [c.as_dict() for c in conditions],
        "comparisons": comparisons,
    }


def _build_solvers_from_env() -> list[Solver]:
    """Default real-run configuration (override by editing or importing)."""
    return [
        SingleModelSolver("qwen2.5-coder:7b"),
        TeamReviewSolver(builder_model="qwen2.5-coder:7b", reviewer_model="phi4-mini"),
    ]


if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Run the AgentForge benchmark")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock solvers (no Ollama)")
    parser.add_argument("--no-tests", action="store_true", help="Skip sandboxed test execution")
    parser.add_argument("--out", default="benchmark_results.json")
    args = parser.parse_args()

    if args.mock:
        solvers = [MockSolver("buggy"), MockSolver("good")]
    else:
        solvers = _build_solvers_from_env()

    report = asyncio.run(run_benchmark(solvers, run_tests=not args.no_tests))
    from benchmarks.report import render_markdown

    Path = __import__("pathlib").Path
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(render_markdown(report))
    print(f"\nWrote {args.out}", file=sys.stderr)

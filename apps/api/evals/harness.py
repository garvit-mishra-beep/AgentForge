"""Eval harness: run behavioral cases and produce a pass/fail report.

A case is a callable (sync or async) returning ``(passed: bool, detail: str)``.
The harness runs them all, tolerates exceptions (counted as failures), and emits
a structured report plus a human-readable summary.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

CaseFn = Callable[[], tuple[bool, str] | Awaitable[tuple[bool, str]]]


@dataclass
class EvalCase:
    name: str
    category: str
    fn: CaseFn
    description: str = ""


@dataclass
class CaseOutcome:
    name: str
    category: str
    passed: bool
    detail: str


async def _run_case(case: EvalCase) -> CaseOutcome:
    try:
        result = case.fn()
        if inspect.isawaitable(result):
            result = await result
        passed, detail = result
    except Exception as e:  # an exception in a case is a failure, not a crash
        passed, detail = False, f"exception: {type(e).__name__}: {e}"
    return CaseOutcome(case.name, case.category, bool(passed), str(detail))


async def run_evals(cases: list[EvalCase]) -> dict:
    outcomes = [await _run_case(c) for c in cases]
    passed = sum(1 for o in outcomes if o.passed)
    by_cat: dict[str, dict[str, int]] = {}
    for o in outcomes:
        cat = by_cat.setdefault(o.category, {"passed": 0, "total": 0})
        cat["total"] += 1
        cat["passed"] += int(o.passed)
    return {
        "total": len(outcomes),
        "passed": passed,
        "failed": len(outcomes) - passed,
        "pass_rate": round(passed / len(outcomes), 4) if outcomes else 0.0,
        "by_category": by_cat,
        "cases": [
            {"name": o.name, "category": o.category, "passed": o.passed, "detail": o.detail}
            for o in outcomes
        ],
    }


def render_report(report: dict) -> str:
    lines = ["# AgentForge Eval Report", ""]
    lines.append(f"**{report['passed']}/{report['total']} passed** "
                 f"({report['pass_rate'] * 100:.1f}%)")
    lines.append("")
    lines.append("| Category | Passed | Total |")
    lines.append("|---|---|---|")
    for cat, stats in sorted(report["by_category"].items()):
        lines.append(f"| {cat} | {stats['passed']} | {stats['total']} |")
    lines.append("")
    failed = [c for c in report["cases"] if not c["passed"]]
    if failed:
        lines.append("## Failures")
        for c in failed:
            lines.append(f"- **{c['name']}** ({c['category']}): {c['detail']}")
    return "\n".join(lines)


if __name__ == "__main__":
    from evals.cases import build_cases

    report = asyncio.run(run_evals(build_cases()))
    print(render_report(report))
    import sys

    sys.exit(0 if report["failed"] == 0 else 1)

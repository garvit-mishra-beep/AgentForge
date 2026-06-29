"""CI wrapper for the agent evaluation framework (offline, mocked providers)."""

import pytest

from evals.cases import build_cases
from evals.harness import run_evals


@pytest.mark.asyncio
async def test_all_eval_cases_pass():
    report = await run_evals(build_cases())
    failed = [c for c in report["cases"] if not c["passed"]]
    assert not failed, f"eval failures: {[(c['name'], c['detail']) for c in failed]}"
    assert report["total"] >= 7


@pytest.mark.asyncio
async def test_eval_categories_present():
    report = await run_evals(build_cases())
    assert {"structured_output", "aggregation", "security", "agent_behavior"} <= set(
        report["by_category"]
    )

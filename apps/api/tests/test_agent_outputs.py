"""Tests for structured agent outputs and the aggregator verdict logic.

Pure-logic tests — no DB/provider needed. Guards TOP_FINDINGS #19 (substring
"fail" verdict replaced by validated ReviewOutput.verdict).
"""

import json

from agents.utils import parse_structured
from models.agent_outputs import Finding, ReviewOutput, Severity, Verdict


def test_review_output_parses_canonical_json():
    text = '{"verdict": "fail", "summary": "bug", "findings": [{"severity": "high", "title": "SQLi", "detail": "x"}]}'
    review = parse_structured(text, ReviewOutput)
    assert review is not None
    assert review.verdict == Verdict.failed
    assert review.findings[0].severity == Severity.high
    assert review.blocking is True


def test_review_output_tolerates_legacy_uppercase_and_synonyms():
    """Older prompts emit PASS/FAIL and major/minor + description/recommendation."""
    text = json.dumps({
        "verdict": "PASS",
        "findings": [
            {"severity": "major", "description": "weak hash", "recommendation": "use bcrypt"},
            {"severity": "minor", "description": "style"},
        ],
    })
    review = parse_structured(text, ReviewOutput)
    assert review is not None
    assert review.verdict == Verdict.passed
    assert review.findings[0].severity == Severity.high
    assert review.findings[0].title == "weak hash"
    assert review.findings[0].suggestion == "use bcrypt"
    assert review.findings[1].severity == Severity.low


def test_parse_structured_returns_none_on_garbage():
    assert parse_structured("not json at all", ReviewOutput) is None
    assert parse_structured("", ReviewOutput) is None
    # Wrong type for findings -> validation error -> None.
    assert parse_structured('{"verdict": "pass", "findings": "oops"}', ReviewOutput) is None


def test_finding_fingerprint_is_stable_and_normalized():
    a = Finding(title="SQL  Injection", file="App/Db.py")
    b = Finding(title="sql injection", file="app/db.py")
    assert a.fingerprint() == b.fingerprint()
    c = Finding(title="XSS", file="app/db.py")
    assert c.fingerprint() != a.fingerprint()


def test_blocking_property():
    assert ReviewOutput(verdict="pass", findings=[{"severity": "critical", "title": "x"}]).blocking
    assert not ReviewOutput(verdict="pass", findings=[{"severity": "low", "title": "x"}]).blocking


def test_auto_aggregate_uses_validated_verdict_not_substring():
    """A finding whose *text* contains 'fail' must NOT flip a passing review."""
    from agents.nodes.aggregator_node import _auto_aggregate

    state = {
        # verdict is pass, but the detail text mentions the word "fail".
        "review": json.dumps({
            "verdict": "pass",
            "findings": [{"severity": "info", "title": "note", "detail": "tests must not fail"}],
        }),
        "tester_output": '{"verdict": "pass", "findings": []}',
        "security_output": '{"verdict": "pass", "findings": []}',
        "architect_output": '{"verdict": "pass", "findings": []}',
    }
    out = json.loads(_auto_aggregate(state))
    assert out["overall_verdict"] == "pass"


def test_auto_aggregate_fails_on_blocking_finding():
    from agents.nodes.aggregator_node import _auto_aggregate

    state = {
        "review": '{"verdict": "pass", "findings": [{"severity": "critical", "title": "RCE"}]}',
        "tester_output": '{"verdict": "pass", "findings": []}',
        "security_output": '{"verdict": "fail", "findings": []}',
        "architect_output": '{"verdict": "pass", "findings": []}',
    }
    out = json.loads(_auto_aggregate(state))
    assert out["overall_verdict"] == "fail"


def test_auto_aggregate_review_needed_on_unparseable():
    from agents.nodes.aggregator_node import _auto_aggregate

    state = {
        "review": "totally not json",
        "tester_output": '{"verdict": "pass", "findings": []}',
        "security_output": '{"verdict": "pass", "findings": []}',
        "architect_output": '{"verdict": "pass", "findings": []}',
    }
    out = json.loads(_auto_aggregate(state))
    assert out["overall_verdict"] == "review_needed"

"""Tests for the feedback-driven learning subsystem."""

import pytest

from app.feedback_service import (
    feedback_stats,
    format_rejected_patterns_for_prompt,
    record_feedback,
    rejected_patterns,
)
from app.main import app

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


def test_format_rejected_patterns_empty():
    assert format_rejected_patterns_for_prompt([]) == ""


def test_format_rejected_patterns_renders_hint():
    out = format_rejected_patterns_for_prompt(
        [{"title": "Prefer f-strings", "rejected": 3, "total": 4}]
    )
    assert "REJECTED" in out
    assert "Prefer f-strings" in out
    assert "3/4" in out


@pytest.mark.asyncio
async def test_submit_feedback_route(client):
    resp = await client.post(
        "/api/v1/feedback",
        json={"title": "Use parameterized query", "decision": "accepted", "severity": "high"},
    )
    assert resp.status_code == 201
    assert "fingerprint" in resp.json()

    stats = await client.get("/api/v1/feedback/stats")
    assert stats.status_code == 200
    assert stats.json()["accepted"] >= 1


@pytest.mark.asyncio
async def test_feedback_route_rejects_bad_decision(client):
    resp = await client.post(
        "/api/v1/feedback",
        json={"title": "x", "decision": "maybe"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rejected_patterns_surfaces_noisy_findings(setup_db):
    """A finding rejected most of the time becomes a learned suppression signal."""
    db = app.state.db
    fp = "deadbeefdeadbeef"
    # 3 rejections, 1 acceptance -> 75% rejection rate over 4 samples.
    for _ in range(3):
        await record_feedback(
            db, user_id=DEMO_USER_ID, fingerprint=fp,
            title="Add docstring", decision="rejected", severity="low",
        )
    await record_feedback(
        db, user_id=DEMO_USER_ID, fingerprint=fp,
        title="Add docstring", decision="accepted", severity="low",
    )

    patterns = await rejected_patterns(db, DEMO_USER_ID)
    assert any(p["fingerprint"] == fp and p["rejected"] == 3 for p in patterns)

    stats = await feedback_stats(db, DEMO_USER_ID)
    assert stats["total"] == 4
    assert stats["rejected"] == 3


@pytest.mark.asyncio
async def test_rejected_patterns_ignores_low_sample_or_accepted(setup_db):
    db = app.state.db
    # Mostly accepted -> not a suppression signal.
    for _ in range(3):
        await record_feedback(
            db, user_id=DEMO_USER_ID, fingerprint="aaaa1111aaaa1111",
            title="Real bug", decision="accepted",
        )
    patterns = await rejected_patterns(db, DEMO_USER_ID)
    assert all(p["fingerprint"] != "aaaa1111aaaa1111" for p in patterns)

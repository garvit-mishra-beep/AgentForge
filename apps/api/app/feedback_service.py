"""Feedback-driven learning service (the quality flywheel).

Records whether developers accept or reject each review finding, then surfaces
the finding *patterns* a given user/project most often rejects. The reviewer
node injects those patterns into its prompt so the critic learns to stop
emitting low-signal noise for that user â€” a data moat no generic model has
(FEATURE_GAP Major Bet #2).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def record_feedback(
    db,
    *,
    user_id: str,
    fingerprint: str,
    title: str,
    decision: str,
    severity: str = "medium",
    project_id: str | None = None,
    task_id: str | None = None,
) -> None:
    """Persist a single accept/reject decision for a finding."""
    if decision not in ("accepted", "rejected"):
        raise ValueError("decision must be 'accepted' or 'rejected'")
    await db.execute(
        """
        INSERT INTO finding_feedback
            (user_id, project_id, task_id, fingerprint, title, severity, decision)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        user_id, project_id, task_id, fingerprint, title, severity, decision,
    )


async def rejected_patterns(
    db, user_id: str, project_id: str | None = None, *, limit: int = 5, min_total: int = 2
) -> list[dict]:
    """Return finding patterns this user rejects most often.

    A pattern is "noisy" when its rejection rate is high across enough samples.
    Scoped to the project when given, otherwise across the user's whole history.
    """
    rows = await db.fetch(
        """
        SELECT fingerprint,
               MAX(title) AS title,
               COUNT(*) FILTER (WHERE decision = 'rejected') AS rejected,
               COUNT(*) AS total
        FROM finding_feedback
        WHERE user_id = $1 AND ($2::uuid IS NULL OR project_id = $2)
        GROUP BY fingerprint
        HAVING COUNT(*) >= $3
           AND COUNT(*) FILTER (WHERE decision = 'rejected')::float / COUNT(*) >= 0.6
        ORDER BY rejected DESC, total DESC
        LIMIT $4
        """,
        user_id, project_id, min_total, limit,
    )
    return [
        {
            "fingerprint": r["fingerprint"],
            "title": r["title"],
            "rejected": r["rejected"],
            "total": r["total"],
        }
        for r in rows
    ]


async def feedback_stats(db, user_id: str) -> dict:
    """Aggregate accept/reject counts for the user (for a dashboard / GET stats)."""
    row = await db.fetchrow(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE decision = 'accepted') AS accepted,
            COUNT(*) FILTER (WHERE decision = 'rejected') AS rejected
        FROM finding_feedback
        WHERE user_id = $1
        """,
        user_id,
    )
    total = row["total"] or 0
    accepted = row["accepted"] or 0
    return {
        "total": total,
        "accepted": accepted,
        "rejected": row["rejected"] or 0,
        "acceptance_rate": round(accepted / total, 3) if total else None,
    }


def format_rejected_patterns_for_prompt(patterns: list[dict]) -> str:
    """Render rejected patterns as a prompt hint for the reviewer. Empty if none."""
    if not patterns:
        return ""
    lines = [
        "LEARNED SIGNAL â€” this developer has previously REJECTED findings like these "
        "as noise. Do not re-raise them unless clearly material:",
    ]
    for p in patterns:
        lines.append(f"- {p['title']} (rejected {p['rejected']}/{p['total']} times)")
    return "\n".join(lines)

"""Render benchmark results as Markdown.

Every number here is computed by :mod:`benchmarks.runner` from the labeled
dataset â€” there are no hardcoded claims.
"""

from __future__ import annotations


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# AgentForge Benchmark Results")
    lines.append("")
    lines.append(f"Tasks: **{report['n_tasks']}** (labeled, deterministic scorer)")
    lines.append("")
    lines.append("| Condition | Pass rate | Mean score | N |")
    lines.append("|---|---|---|---|")
    for c in report["conditions"]:
        lines.append(
            f"| {c['name']} | {c['pass_rate'] * 100:.1f}% | {c['mean_score']:.3f} | {c['n']} |"
        )
    lines.append("")

    if report["comparisons"]:
        lines.append("## Lift vs baseline")
        lines.append("")
        lines.append("| Condition | vs | Pass-rate delta | Lift | Mean-score delta |")
        lines.append("|---|---|---|---|---|")
        for cmp in report["comparisons"]:
            lift = cmp["pass_rate_lift_pct"]
            lift_str = f"{lift:+.1f}%" if lift is not None else "n/a"
            lines.append(
                f"| {cmp['condition']} | {cmp['vs']} | "
                f"{cmp['pass_rate_delta'] * 100:+.1f}pp | {lift_str} | "
                f"{cmp['mean_score_delta']:+.3f} |"
            )
        lines.append("")
        lines.append(
            "> Lift is the relative improvement in pass rate of the multi-agent "
            "condition over the single-model baseline, measured on this dataset."
        )
    return "\n".join(lines)

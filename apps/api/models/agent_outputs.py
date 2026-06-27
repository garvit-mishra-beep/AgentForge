"""Structured, validated schemas for agent outputs.

Agents are prompted to emit JSON, but historically nothing validated it and the
aggregator decided pass/fail by a substring search for ``"fail"`` in free text
(TOP_FINDINGS #19) — a brittle, easily-fooled heuristic. These Pydantic models
give every consumer (aggregator, delivery, GitHub bot, feedback flywheel, eval
harness) a single typed contract for findings and verdicts.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

# Synonyms emitted by various local models, normalized to the canonical enums.
_SEVERITY_SYNONYMS = {
    "blocker": "critical", "crit": "critical",
    "major": "high", "high": "high",
    "minor": "low", "moderate": "medium", "med": "medium",
    "nit": "info", "informational": "info", "note": "info",
}
_VERDICT_SYNONYMS = {
    "pass": "pass", "passed": "pass", "ok": "pass", "approve": "pass", "approved": "pass",
    "fail": "fail", "failed": "fail", "reject": "fail", "rejected": "fail", "block": "fail",
    "review_needed": "review_needed", "needs_review": "review_needed",
    "review": "review_needed", "warn": "review_needed",
}


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Verdict(str, Enum):
    passed = "pass"
    failed = "fail"
    review_needed = "review_needed"


class Finding(BaseModel):
    """A single issue raised by a reviewing agent."""

    severity: Severity = Severity.medium
    title: str
    detail: str = ""
    file: str | None = None
    line: int | None = None
    suggestion: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_keys(cls, data):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # Legacy/alt field names used by older prompts.
        if "title" not in data:
            data["title"] = data.get("description") or data.get("message") or "Finding"
        if "detail" not in data and "description" in data:
            data["detail"] = data["description"]
        if "suggestion" not in data and "recommendation" in data:
            data["suggestion"] = data["recommendation"]
        return data

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, v):
        if isinstance(v, str):
            return _SEVERITY_SYNONYMS.get(v.strip().lower(), v.strip().lower())
        return v

    def fingerprint(self) -> str:
        """Stable identity used for dedup and feedback learning.

        Normalizes the title and file so cosmetically-different phrasings of the
        same issue collapse to one key.
        """
        import hashlib

        norm_title = " ".join(self.title.lower().split())
        norm_file = (self.file or "").strip().lower()
        return hashlib.sha256(f"{norm_file}|{norm_title}".encode()).hexdigest()[:16]


class ReviewOutput(BaseModel):
    verdict: Verdict = Verdict.review_needed
    summary: str = ""
    findings: list[Finding] = Field(default_factory=list)

    @field_validator("verdict", mode="before")
    @classmethod
    def _normalize_verdict(cls, v):
        if isinstance(v, str):
            return _VERDICT_SYNONYMS.get(v.strip().lower(), v.strip().lower())
        return v

    @property
    def blocking(self) -> bool:
        return self.verdict == Verdict.failed or any(
            f.severity in (Severity.critical, Severity.high) for f in self.findings
        )


class PlanStep(BaseModel):
    description: str
    rationale: str | None = None


class PlanOutput(BaseModel):
    plan_summary: str = ""
    steps: list[PlanStep] = Field(default_factory=list)


class FileChange(BaseModel):
    path: str
    content: str = ""
    action: str = "create"  # create | modify | delete


class BuilderOutput(BaseModel):
    summary: str = ""
    files: list[FileChange] = Field(default_factory=list)


class DeliveryOutput(BaseModel):
    verdict: Verdict = Verdict.review_needed
    delivery_summary: str = ""

"""Quick Review route with Redis-backed store, model registry, worker pool,
semantic comparison, and structured observability."""

import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from agents.utils import load_prompt_template
from app.auth import require_user
from core.config import settings
from core.model_registry import get_registry
from core.observability import emit
from core.providers import AIProviderError, ChatResponse, get_provider
from core.redis import rate_limit_check, review_store_cleanup, review_store_get, review_store_set, review_store_update
from core.task_tracker import tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["review"])

# ── Schemas ─────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=settings.review_max_code_length)
    language: str | None = None


class ReviewIssue(BaseModel):
    severity: str
    title: str
    line: int | None = None
    description: str
    suggestion: str


class ReviewComparison(BaseModel):
    baseline_issues: list[ReviewIssue] = Field(default_factory=list)
    bugs_single_would_miss: int = 0
    summary: str = ""


class ReviewResponse(BaseModel):
    review_id: str
    status: str
    issues: list[ReviewIssue] = Field(default_factory=list)
    summary: str = ""
    comparison: ReviewComparison | None = None
    duration_ms: float = 0.0
    error: str | None = None

    model_config = {"json_schema_extra": {"example": {"review_id": "uuid", "status": "queued"}}}


# ── Background task dispatch ───────────────────────────────────────────

_worker_task: asyncio.Task | None = None


def start_worker() -> None:
    logger.info("Review background dispatch ready")


def stop_worker() -> None:
    logger.info("Review background dispatch stopped")


# ── Language detection ─────────────────────────────────────────────────

_LANG_KEYWORDS: dict[str, list[str]] = {
    "python": ["def ", "import ", "class ", "async def", "except "],
    "javascript": ["function ", "const ", "let ", "=>", "console."],
    "typescript": [": string", ": number", ": boolean", "interface ", "type "],
    "java": ["public class", "private ", "static void", "System.out"],
    "go": ["func ", "package ", "import (", "fmt."],
    "rust": ["fn ", "let mut", "impl ", "pub "],
    "sql": ["SELECT", "FROM", "WHERE", "INSERT ", "CREATE TABLE"],
    "ruby": ["def ", "end", "require ", "class ", "attr_"],
}


def _detect_language(code: str) -> str:
    ext_hints = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript", ".jsx": "javascript", ".java": "java",
        ".go": "go", ".rs": "rust", ".rb": "ruby", ".sql": "sql",
    }
    for ext, lang in ext_hints.items():
        if ext in code[:200]:
            return lang

    scores: dict[str, int] = {}
    for lang, keywords in _LANG_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in code)
        if score > 0:
            scores[lang] = score
    if not scores:
        return "unknown"
    return max(scores, key=scores.get)


# ── Prompt loading ─────────────────────────────────────────────────────

_builder_template = load_prompt_template("review_quick_builder.jinja2").get_template("review_quick_builder.jinja2")
_reviewer_template = load_prompt_template("review_quick_reviewer.jinja2").get_template("review_quick_reviewer.jinja2")


# ── JSON parsing with retry ────────────────────────────────────────────

def _validate_json(text: str) -> dict:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError("Model output is not valid JSON") from e


def _parse_json(text: str) -> dict | None:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


async def _call_with_json_retry(
    provider,
    model: str,
    system_prompt: str,
    user_message: str,
    timeout_s: float = 45.0,
    max_tokens: int = 1024,
) -> ChatResponse:
    for attempt in range(2):
        result = await provider.chat(
            model, system_prompt, user_message,
            max_tokens=max_tokens, timeout_s=timeout_s,
        )
        try:
            _validate_json(result.content)
            return result
        except ValueError:
            logger.warning("JSON parse failed (attempt %d/2) for model %s", attempt + 1, model)
            if attempt == 0:
                system_prompt += "\nReturn valid JSON only."
                continue
            raise


# ── Pipeline stages ────────────────────────────────────────────────────

async def _run_baseline(code: str, language: str, timeout_s: float = 45.0) -> tuple[list[dict], str, str]:
    registry = get_registry()
    model, fallback = await registry.resolve("baseline")
    provider = get_provider(model)

    system_prompt = (
        f"You are a code reviewer. Review the following {language} code.\n"
        "Output JSON only:\n"
        "{\n"
        '  "issues": [\n'
        "    {\n"
        '      "severity": "critical|major|minor",\n'
        '      "title": "short title",\n'
        '      "line": <line_number or null>,\n'
        '      "description": "what is wrong",\n'
        '      "suggestion": "how to fix"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "1-2 sentence summary"\n'
        "}\n"
        "Focus on real bugs, security issues, logic errors.\n"
        'If correct, return {"issues": [], "summary": "No issues found."}'
    )

    result = await _call_with_json_retry(
        provider, model, system_prompt, code,
        timeout_s=timeout_s, max_tokens=1024,
    )
    data = _parse_json(result.content) or {"issues": [], "summary": ""}
    return data.get("issues", []), data.get("summary", ""), model


async def _run_builder(code: str, timeout_s: float = 30.0) -> tuple[str, str]:
    registry = get_registry()
    model, fallback = await registry.resolve("builder")
    provider = get_provider(model)
    system_prompt = _builder_template.render(code=code)

    result = await _call_with_json_retry(
        provider, model, system_prompt, code,
        timeout_s=timeout_s, max_tokens=512,
    )
    return result.content, model


async def _run_reviewer(
    code: str,
    analysis: str,
    language: str,
    timeout_s: float = 45.0,
) -> tuple[list[dict], str, str]:
    registry = get_registry()
    model, fallback = await registry.resolve("reviewer")
    provider = get_provider(model)
    system_prompt = _reviewer_template.render(code=code, analysis=analysis)

    result = await _call_with_json_retry(
        provider, model, system_prompt, code,
        timeout_s=timeout_s, max_tokens=1024,
    )
    data = _parse_json(result.content) or {"issues": [], "summary": ""}
    return data.get("issues", []), data.get("summary", ""), model


# ── Semantic comparison ────────────────────────────────────────────────

def _tokenize(title: str) -> set[str]:
    return set(title.lower().replace("-", " ").replace("_", " ").split())


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _count_unique_issues_semantic(multi_issues: list[dict], baseline_issues: list[dict], threshold: float = 0.3) -> int:
    if not baseline_issues:
        return len(multi_issues)
    baseline_tokens = [_tokenize(i.get("title", "")) for i in baseline_issues if i.get("title")]
    if not baseline_tokens:
        return len(multi_issues)
    unique = 0
    for mi in multi_issues:
        mt = _tokenize(mi.get("title", ""))
        if not mt:
            unique += 1
            continue
        matched = any(_jaccard_similarity(mt, bt) >= threshold for bt in baseline_tokens)
        if not matched:
            unique += 1
    return unique


# ── Issue parsing ──────────────────────────────────────────────────────

def _parse_issues(raw: list[dict]) -> list[ReviewIssue]:
    issues: list[ReviewIssue] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity", "minor")
        if severity not in ("critical", "major", "minor"):
            severity = "minor"
        issues.append(ReviewIssue(
            severity=severity,
            title=item.get("title", "Unknown issue"),
            line=item.get("line"),
            description=item.get("description", ""),
            suggestion=item.get("suggestion", ""),
        ))
    return issues


# ── Background pipeline ────────────────────────────────────────────────

PIPELINE_TIMEOUT_S = 180


async def _run_review_pipeline(data: dict) -> None:
    review_id = data["review_id"]
    code = data["code"].strip()
    language = data["language"] or _detect_language(code)
    start = time.monotonic()

    try:
        await review_store_update(review_id, {"status": "analyzing"})

        baseline_future = _run_baseline(code, language)
        builder_future = _run_builder(code)

        (baseline_issues_raw, baseline_summary, model_baseline), \
            (builder_content, model_builder) = await asyncio.gather(
                baseline_future, builder_future,
            )

        await review_store_update(review_id, {"status": "reviewing"})

        issues_raw, summary, model_reviewer = await asyncio.wait_for(
            _run_reviewer(code, builder_content, language),
            timeout=45.0,
        )

        unique_count = _count_unique_issues_semantic(issues_raw, baseline_issues_raw)
        duration_ms = (time.monotonic() - start) * 1000

        await review_store_update(review_id, {
            "status": "completed",
            "issues": issues_raw,
            "summary": summary,
            "baseline_issues": baseline_issues_raw,
            "duration_ms": duration_ms,
            "completed_at": time.time(),
            "model_baseline": model_baseline,
            "model_builder": model_builder,
            "model_reviewer": model_reviewer,
        })

        logger.info(
            "Review %s completed: %d issues, %d unique vs baseline (%.1fs)",
            review_id, len(issues_raw), unique_count, duration_ms / 1000,
        )
        emit("review_completed", {
            "review_id": review_id,
            "duration_ms": duration_ms,
            "issues": len(issues_raw),
            "unique": unique_count,
            "models": f"{model_baseline}/{model_builder}/{model_reviewer}",
        })

    except asyncio.TimeoutError:
        duration_ms = (time.monotonic() - start) * 1000
        logger.error("Review pipeline timed out for %s", review_id)
        await review_store_update(review_id, {
            "status": "failed",
            "error": "Pipeline timed out",
            "duration_ms": duration_ms,
            "completed_at": time.time(),
        })
        emit("review_failed", {"review_id": review_id, "error": "timeout", "duration_ms": duration_ms})

    except Exception as e:
        duration_ms = (time.monotonic() - start) * 1000
        logger.exception("Review pipeline failed for %s", review_id)
        await review_store_update(review_id, {
            "status": "failed",
            "error": str(e),
            "duration_ms": duration_ms,
            "completed_at": time.time(),
        })
        emit("review_failed", {"review_id": review_id, "error": str(e), "duration_ms": duration_ms})


# ── Routes ─────────────────────────────────────────────────────────────

@router.post("")
async def quick_review(
    body: ReviewRequest,
    request: Request,
    user_id: str = Depends(require_user),
) -> ReviewResponse:
    await review_store_cleanup()

    ip = request.client.host if request.client else "unknown"
    allowed = await rate_limit_check(ip, limit=settings.review_rate_limit, window=settings.review_rate_window)
    if not allowed:
        emit("rate_limit_hit", {"ip": ip})
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {settings.review_rate_limit} reviews per hour per IP.",
        )

    code = body.code.strip()
    language = body.language or _detect_language(code)
    review_id = str(uuid.uuid4())

    task_data = {
        "review_id": review_id,
        "status": "queued",
        "code": code,
        "language": language,
        "issues": [],
        "summary": "",
        "baseline_issues": [],
        "duration_ms": 0.0,
        "error": None,
        "created_at": time.time(),
        "completed_at": None,
        "model_baseline": "",
        "model_builder": "",
        "model_reviewer": "",
    }

    await review_store_set(review_id, task_data)

    tracker.create_task(
        _run_review_pipeline(task_data),
        name=f"review-{review_id[:8]}",
    )

    emit("review_queued", {"review_id": review_id, "language": language, "size_bytes": len(code)})
    logger.info("Review %s queued (%dB, %s)", review_id, len(code), language)

    return ReviewResponse(review_id=review_id, status="queued")


@router.get("/{review_id}")
async def get_review(
    review_id: str,
    user_id: str = Depends(require_user),
) -> ReviewResponse:
    data = await review_store_get(review_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Review not found")

    resp = ReviewResponse(
        review_id=data["review_id"],
        status=data["status"],
        error=data.get("error"),
        duration_ms=data.get("duration_ms", 0.0),
    )

    if data["status"] in ("completed", "failed"):
        issues = _parse_issues(data.get("issues", []))
        baseline_issues = _parse_issues(data.get("baseline_issues", []))
        unique_count = _count_unique_issues_semantic(data.get("issues", []), data.get("baseline_issues", []))

        resp.issues = issues
        resp.summary = data.get("summary", "")
        resp.comparison = ReviewComparison(
            baseline_issues=baseline_issues,
            bugs_single_would_miss=unique_count,
            summary=(
                f"Multi-agent review found {len(issues)} issue{'s' if len(issues) != 1 else ''}. "
                f"Baseline found {len(baseline_issues)}. "
                f"{unique_count} issue{'s' if unique_count != 1 else ''} unique to multi-agent review."
            ),
        )

    return resp

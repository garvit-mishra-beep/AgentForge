"""Endpoints for code review workflow."""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user
from core.config import settings
from core.dependencies import get_db
from core.model_registry import get_registry
from core.redis import (
    check_rate_limit,
    get_review_state,
    review_store_cleanup,
    review_store_update,
)
from models.schemas import (
    LanguageDetectionResponse,
    ReviewRequest,
    ReviewResponse,
    ReviewResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["review"])

# In-memory store for demo mode (would be replaced with Redis/DB in production)
_reviews: dict[str, dict[str, Any]] = {}


def start_worker() -> None:
    logger.info("Review background worker started (no-op)")


def stop_worker() -> None:
    logger.info("Review background worker stopped (no-op)")


async def _run_baseline(code: str, language: str, user_id: str, db: AsyncSession | None = None) -> tuple:
    """Run baseline analysis on the code."""
    # Get baseline model (first in baseline chain)
    registry = get_registry()
    baseline_chain = registry.get_legacy_chain("baseline")
    model = baseline_chain[0] if baseline_chain else "claude-3-5-sonnet"

    # Get provider for user
    provider, _ = await registry.get_provider_for_user(user_id, model, db_session=db)

    # Run analysis
    system_prompt = """Analyze the following code and provide:
    1. What the code does (purpose)
    2. Programming language
    3. Dependencies/libraries used
    4. Data flow description
    5. Potential problem areas or bugs

    Respond in JSON format with keys: purpose, language, dependencies (list), data_flow, problem_areas (list)"""

    user_message = f"Analyze this {language} code:\n\n{code}"

    try:
        response = await provider.chat(
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1000,
            timeout_s=30.0,
        )

        # Parse JSON response
        try:
            result = json.loads(response.content)
            return (
                result.get("problem_areas", []),
                result.get("summary", "Analysis complete"),
                model
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback if response isn't valid JSON
            return (
                [{"severity": "unknown", "title": "Analysis completed",
                  "description": str(response.content)[:200], "suggestion": "Review manually"}],
                "Analysis completed (non-JSON response)",
                model
            )
    except Exception as e:
        logger.error(f"Baseline analysis failed: {e}")
        return (
            [{"severity": "error", "title": "Analysis failed",
              "description": str(e), "suggestion": "Check system logs"}],
            "Analysis failed",
            model
        )


async def _run_builder(code: str, user_id: str, db: AsyncSession | None = None) -> tuple:
    """Run builder to generate improved version of the code."""
    # Get builder model (first in builder chain)
    registry = get_registry()
    builder_chain = registry.get_legacy_chain("builder")
    model = builder_chain[0] if builder_chain else "gpt-4o"

    # Get provider for user
    provider, _ = await registry.get_provider_for_user(user_id, model, db_session=db)

    # Run code improvement
    system_prompt = """You are an expert software engineer. Improve the provided code by:
    1. Fixing any bugs or issues
    2. Improving code quality and readability
    3. Adding best practices
    4. Maintaining the same functionality

    Respond with ONLY the improved code. No explanations, no additional text."""

    user_message = f"Improve this code:\n\n{code}"

    try:
        response = await provider.chat(
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=2000,
            timeout_s=30.0,
        )

        return (response.content.strip(), model)
    except Exception as e:
        logger.error(f"Builder failed: {e}")
        return (f"# Error generating improved code: {str(e)}", model)


async def _run_reviewer(
    code: str, builder_content: str, language: str, user_id: str, db: AsyncSession | None = None
) -> tuple:
    """Run reviewer to find issues in both original and improved code."""
    # Get reviewer model (first in reviewer chain)
    registry = get_registry()
    reviewer_chain = registry.get_legacy_chain("reviewer")
    model = reviewer_chain[0] if reviewer_chain else "claude-3-5-sonnet"

    # Get provider for user
    provider, _ = await registry.get_provider_for_user(user_id, model, db_session=db)

    # Review both versions and find differences
    system_prompt = """You are an expert code reviewer. Compare the original code with the
    improved version and identify:
    1. Issues that were fixed in the improved version
    2. Issues that remain in the improved version
    3. Any new issues introduced in the improved version

    Focus on: bugs, security issues, performance issues, code quality, best practices.

    Output JSON only with this structure:
    {
        "issues": [
            {
                "severity": "critical|major|minor|info",
                "title": "Brief issue title",
                "line": line_number_or_null,
                "description": "Detailed description",
                "suggestion": "How to fix it"
            }
        ],
        "summary": "Brief summary of findings"
    }

    If outputting line numbers, refer to the improved version. If an issue applies
    to both versions or cannot be localized, set line to null."""

    user_message = f"""Original {language} code:
    ```{language}
    {code}
    ```

    Improved {language} code:
    ```{language}
    {builder_content}
    ```

    Compare and identify issues:"""

    try:
        response = await provider.chat(
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1500,
            timeout_s=30.0,
        )

        # Parse JSON response
        try:
            result = json.loads(response.content)
            issues = result.get("issues", [])
            # Ensure each issue has required fields
            for issue in issues:
                if "severity" not in issue:
                    issue["severity"] = "unknown"
                if "title" not in issue:
                    issue["title"] = "Issue found"
                if "description" not in issue:
                    issue["description"] = str(issue.get("description", ""))
                if "suggestion" not in issue:
                    issue["suggestion"] = "Review manually"
            return (
                issues,
                result.get("summary", "Review completed"),
                model
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse reviewer response: {e}")
            # Fallback: create a basic issue from the response
            return (
                [{"severity": "unknown", "title": "Review completed",
                  "description": str(response.content)[:500], "suggestion": "Review manually"}],
                "Review completed (non-JSON response)",
                model
            )
    except Exception as e:
        logger.error(f"Reviewer failed: {e}")
        return (
            [{"severity": "error", "title": "Review failed",
              "description": str(e), "suggestion": "Check system logs"}],
            "Review failed",
            model
        )


@router.post("", response_model=ReviewResponse)
async def submit_review(
    request: ReviewRequest,
    http_request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    # Clean up old reviews
    await review_store_cleanup()

    # Rate limiting check
    ip = http_request.client.host if http_request.client else "unknown"
    allowed = await check_rate_limit(
        ip,
        limit=settings.review_rate_limit,
        window=settings.review_rate_window
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.review_rate_limit} reviews per hour per IP.",
        )

    # Generate review ID
    review_id = str(uuid.uuid4())

    # Initialize review state
    await review_store_update(
        review_id,
        {
            "id": review_id,
            "status": "queued",
            "code": request.code,
            "language": request.language,
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )

    # Start background processing
    db_pool = http_request.app.state.db
    asyncio.create_task(_process_review(review_id, request.code, request.language or "text", user_id, db_pool))

    return ReviewResponse(
        review_id=review_id,
        status="queued",
    )


async def _process_review(review_id: str, code: str, language: str, user_id: str, db: AsyncSession):
    """Background task to process a review."""
    try:
        # Update status to analyzing
        await review_store_update(review_id, {"status": "analyzing"})

        # Run baseline and builder in parallel
        baseline_future = _run_baseline(code, language, user_id, db)
        builder_future = _run_builder(code, user_id, db)

        (baseline_issues_raw, baseline_summary, model_baseline), \
            (builder_content, model_builder) = await asyncio.gather(
                baseline_future, builder_future,
            )

        await review_store_update(review_id, {"status": "reviewing"})

        # Run reviewer
        issues_raw, summary, model_reviewer = await asyncio.wait_for(
            _run_reviewer(code, builder_content, language, user_id, db),
            timeout=45.0,
        )

        # Format issues for response
        formatted_issues = []
        for issue in issues_raw:
            formatted_issues.append({
                "id": str(uuid.uuid4()),
                "severity": issue.get("severity", "unknown"),
                "title": issue.get("title", "Issue"),
                "line": issue.get("line"),
                "description": issue.get("description", ""),
                "suggestion": issue.get("suggestion", "Review manually"),
            })

        # Calculate base models used
        base_models = [model_baseline, model_builder]
        if model_reviewer not in base_models:
            base_models.append(model_reviewer)

        # Store results
        await review_store_update(
            review_id,
            {
                "status": "completed",
                "baseline_issues": baseline_issues_raw,
                "builder_output": builder_content,
                "review_issues": formatted_issues,
                "summary": summary,
                "base_models": base_models,
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )

    except TimeoutError:
        await review_store_update(
            review_id,
            {
                "status": "failed",
                "error": "Review timed out",
                "failed_at": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Review processing failed: {e}")
        await review_store_update(
            review_id,
            {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now(UTC).isoformat(),
            }
        )


@router.get("/{review_id}", response_model=ReviewResult)
async def get_review(
    review_id: str,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get review results by ID."""
    # Get review state
    review_data = await get_review_state(review_id)

    if not review_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_id} not found",
        )

    # Check if user owns this review (or if it's a demo review)
    if review_data.get("user_id") != user_id and not review_data.get("user_id") == "demo":
        # Allow demo user to view demo reviews
        if not (user_id == "demo" and review_data.get("user_id") == "demo"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this review",
            )

    # Format response based on status
    review_status = review_data.get("status", "unknown")

    if review_status == "completed":
        return ReviewResult(
            review_id=review_id,
            status=review_status,
            baseline_issues=review_data.get("baseline_issues", []),
            builder_output=review_data.get("builder_output", ""),
            review_issues=review_data.get("review_issues", []),
            summary=review_data.get("summary", ""),
            model_used=review_data.get("base_models", ["unknown"])[0] if review_data.get("base_models") else "unknown",
            created_at=review_data.get("created_at"),
            completed_at=review_data.get("completed_at"),
        )
    elif review_status == "failed":
        return ReviewResult(
            review_id=review_id,
            status=review_status,
            error=review_data.get("error", "Unknown error"),
            created_at=review_data.get("created_at"),
            failed_at=review_data.get("failed_at"),
        )
    else:
        # queued, analyzing, reviewing
        return ReviewResult(
            review_id=review_id,
            status=review_status,
            created_at=review_data.get("created_at"),
        )


@router.get("/language/detect", response_model=LanguageDetectionResponse)
async def detect_language(code: str):
    """Detect programming language from code snippet."""
    # Simple language detection based on common patterns
    # In production, this would use a proper library or ML model

    code_lower = code.lower().strip()

    # Python indicators
    if any(keyword in code_lower for keyword in ["def ", "import ", "from ", "if __name__", "print("]):
        return LanguageDetectionResponse(language="python", confidence=0.9)

    # JavaScript/TypeScript indicators
    if any(keyword in code_lower for keyword in ["function ", "var ", "let ", "const ", "=>", "console.log"]):
        if "interface " in code_lower or "type " in code_lower or ": " in code_lower:
            return LanguageDetectionResponse(language="typescript", confidence=0.8)
        return LanguageDetectionResponse(language="javascript", confidence=0.9)

    # Java indicators
    if any(keyword in code_lower for keyword in ["public class", "public static void main", "system.out.println"]):
        return LanguageDetectionResponse(language="java", confidence=0.9)

    # C/C++ indicators
    if any(keyword in code_lower for keyword in ["#include", "int main()", "printf(", "cout <<"]):
        if "cout <<" in code_lower or "namespace " in code_lower:
            return LanguageDetectionResponse(language="cpp", confidence=0.8)
        return LanguageDetectionResponse(language="c", confidence=0.8)

    # Go indicators
    if any(keyword in code_lower for keyword in ["package ", "func ", "import ", "fmt.println"]):
        return LanguageDetectionResponse(language="go", confidence=0.9)

    # Rust indicators
    if any(keyword in code_lower for keyword in ["fn ", "let mut", "println!", "use ", "impl "]):
        return LanguageDetectionResponse(language="rust", confidence=0.9)

    # SQL indicators
    if any(keyword in code_lower for keyword in ["select ", "insert into", "update ", "delete from", "create table"]):
        return LanguageDetectionResponse(language="sql", confidence=0.8)

    # HTML indicators
    if any(keyword in code_lower for keyword in ["<!doctype", "<html", "<body", "<div "]):
        return LanguageDetectionResponse(language="html", confidence=0.8)

    # CSS indicators
    if any(keyword in code_lower for keyword in ["{", "color:", "background:", "font-size:"]):
        # Check if it looks like CSS (has properties)
        if ":" in code_lower and "{" in code_lower:
            return LanguageDetectionResponse(language="css", confidence=0.7)

    # Default to text if no match
    return LanguageDetectionResponse(language="text", confidence=0.5)


# Legacy endpoint for backward compatibility
@router.get("/{review_id}/status")
async def get_review_status_legacy(
    review_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    """Get review status (legacy endpoint)."""

    review_data = await get_review_state(review_id)

    if not review_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_id} not found",
        )

    # Check if user owns this review (or if it's a demo review)
    if review_data.get("user_id") != user_id and not review_data.get("user_id") == "demo":
        # Allow demo user to view demo reviews
        if not (user_id == "demo" and review_data.get("user_id") == "demo"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this review",
            )

    return {"status": review_data.get("status", "unknown")}

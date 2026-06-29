"""GitHub App webhook + status routes with enhanced integration."""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.github import handle_pull_request_event, verify_webhook_signature
from app.integrations.github_enhanced import review_pull_request as enhanced_review_pr
from app.integrations.github_enhanced import synchronize_repository as enhanced_sync_repo
from core.config import settings
from core.dependencies import get_db
from core.observability import emit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/github", tags=["github"])


@router.get("/status")
async def github_status():
    """Report whether the GitHub App is configured (no secrets leaked)."""
    return {
        "configured": bool(
            settings.github_app_id
            and settings.github_app_private_key
            and settings.github_webhook_secret
        ),
        "app_id_set": bool(settings.github_app_id),
        "enhanced_features": {
            "repository_synchronization": True,
            "comprehensive_pr_reviews": True,
            "multi_agent_analysis": True,
            "automated_feedback": True
        }
    }


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Receive a GitHub App webhook, verify its signature, and dispatch.

    Routes events to appropriate handlers - basic or enhanced based on configuration.
    """
    if not settings.github_webhook_secret:
        raise HTTPException(status_code=503, detail="GitHub integration not configured")

    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_webhook_signature(settings.github_webhook_secret, body, signature):
        emit("github_webhook_bad_signature", {})
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if event == "ping":
        return {"ok": True, "pong": True}

    if event == "pull_request":
        # Check if enhanced review is enabled (could be configured via settings or repo-specific)
        use_enhanced = getattr(settings, 'github_use_enhanced_review', True)

        if use_enhanced:
            # Use enhanced multi-agent review
            background_tasks.add_task(
                _safe_enhanced_handle,
                payload
            )
        else:
            # Use basic review
            background_tasks.add_task(
                _safe_handle,
                payload
            )
        return {"ok": True, "queued": True, "enhanced": use_enhanced}

    # Handle repository events with enhanced synchronization
    if event == "repository":
        background_tasks.add_task(
            _safe_handle_repository_event,
            payload
        )
        return {"ok": True, "handled": True, "enhanced": True}

    return {"ok": True, "ignored": event}


async def _safe_handle(payload: dict) -> None:
    """Safe handler for basic PR review (existing functionality)."""
    try:
        result = await handle_pull_request_event(payload)
        emit("github_pr_reviewed", result)
        logger.info("GitHub PR reviewed (basic): %s", result)
    except Exception as e:
        logger.exception("GitHub PR review failed: %s", e)
        emit("github_pr_review_error", {"error": str(e)})


async def _safe_enhanced_handle(payload: dict) -> None:
    """Safe handler for enhanced PR review."""
    try:
        # Extract PR information
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        installation_data = payload.get("installation", {})

        if not all([pr_data, repo_data, installation_data]):
            logger.warning("Incomplete payload for enhanced PR review")
            return

        pr_number = pr_data.get("number")
        repo_full_name = repo_data.get("full_name")
        installation_id = installation_data.get("id")

        if not all([pr_number, repo_full_name, installation_id]):
            logger.warning("Missing required data for enhanced PR review")
            return

        # Perform enhanced review
        result = await enhanced_review_pr(
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            include_security=True,
            include_performance=True,
            include_style=True
        )

        emit("github_pr_reviewed_enhanced", result)
        logger.info("GitHub PR reviewed (enhanced): %s", result)

    except Exception as e:
        logger.exception("GitHub enhanced PR review failed: %s", e)
        emit("github_pr_review_error_enhanced", {"error": str(e)})


async def _safe_handle_repository_event(payload: dict) -> None:
    """Safe handler for repository events with enhanced synchronization."""
    try:
        action = payload.get("action")
        repo_data = payload.get("repository", {})
        installation_data = payload.get("installation", {})

        if not all([action, repo_data, installation_data]):
            logger.warning("Incomplete payload for repository webhook")
            return

        repo_full_name = repo_data.get("full_name")
        installation_id = installation_data.get("id")

        if not all([repo_full_name, installation_id]):
            logger.warning("Missing required data for repository webhook")
            return

        # Handle different repository actions
        if action in ["created", "edited"]:
            # Synchronize repository on creation or edit
            result = await enhanced_sync_repo(
                installation_id=installation_id,
                repo_full_name=repo_full_name
            )
            emit("github_repository_synchronized_enhanced", result)
            logger.info("Repository synchronized (enhanced): %s", result)

        elif action == "deleted":
            # Handle repository deletion
            emit("github_repository_deleted", {
                "installation_id": installation_id,
                "repository": repo_full_name
            })
            logger.info("Repository deleted: %s", repo_full_name)

    except Exception as e:
        logger.exception("Repository webhook handling failed: %s", e)
        emit("github_repository_webhook_error", {"error": str(e)})

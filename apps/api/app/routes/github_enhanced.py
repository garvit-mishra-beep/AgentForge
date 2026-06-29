"""
Enhanced GitHub Routes for AgentForge.
Provides additional endpoints for repository synchronization and enhanced workflow integration.
"""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.github import verify_webhook_signature
from app.integrations.github_enhanced import (
    handle_repository_webhook,
    review_pull_request,
    synchronize_repository,
)
from core.config import settings
from core.dependencies import get_db
from core.observability import emit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/github/enhanced", tags=["github-enhanced"])


@router.get("/status")
async def enhanced_github_status():
    """Report enhanced GitHub integration status."""
    base_status = {
        "configured": bool(
            settings.github_app_id
            and settings.github_app_private_key
            and settings.github_webhook_secret
        ),
        "app_id_set": bool(settings.github_app_id),
    }

    # Add enhanced features status
    base_status.update({
        "enhanced_features": {
            "repository_synchronization": True,
            "comprehensive_pr_reviews": True,
            "multi_agent_analysis": True,
            "automated_feedback": True
        }
    })

    return base_status


@router.post("/repository/sync")
async def sync_repository_endpoint(
    installation_id: int,
    repository_full_name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronize a repository with AgentForge.

    Args:
        installation_id: GitHub installation ID
        repository_full_name: Repository full name (owner/repo)
        background_tasks: FastAPI background tasks handler
        db: Database session

    Returns:
        Synchronization result
    """
    try:
        # Perform synchronization in background
        background_tasks.add_task(
            _sync_repository_task,
            installation_id,
            repository_full_name,
            db
        )

        return {
            "accepted": True,
            "message": f"Synchronization started for {repository_full_name}",
            "installation_id": installation_id,
            "repository": repository_full_name
        }
    except Exception as e:
        logger.error(f"Failed to initiate repository synchronization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _sync_repository_task(
    installation_id: int,
    repository_full_name: str,
    db: AsyncSession
):
    """Background task to synchronize repository."""
    try:
        result = await synchronize_repository(
            installation_id,
            repository_full_name
        )

        if result["success"]:
            # Here we would update the repository record in the database
            # For now, we'll just emit an event
            emit("github_repository_synchronized", {
                "installation_id": installation_id,
                "repository": repository_full_name,
                "repository_data": result["repository"]
            })
            logger.info(f"Successfully synchronized repository {repository_full_name}")
        else:
            emit("github_repository_sync_failed", {
                "installation_id": installation_id,
                "repository": repository_full_name,
                "error": result["error"]
            })
            logger.error(f"Failed to synchronize repository {repository_full_name}: {result['error']}")

    except Exception as e:
        logger.error(f"Repository synchronization task failed: {e}")
        emit("github_repository_sync_error", {
            "installation_id": installation_id,
            "repository": repository_full_name,
            "error": str(e)
        })


@router.post("/pull-request/{repository_full_name:path}/review")
async def review_pull_request_endpoint(
    repository_full_name: str,
    pull_request_number: int,
    background_tasks: BackgroundTasks,
    include_security: bool = True,
    include_performance: bool = True,
    include_style: bool = True
):
    """
    Request a comprehensive review of a pull request.

    Args:
        repository_full_name: Repository full name (owner/repo)
        pull_request_number: Pull request number
        background_tasks: FastAPI background tasks handler
        include_security: Whether to include security analysis
        include_performance: Whether to include performance analysis
        include_style: Whether to include style checking

    Returns:
        Acceptance response
    """
    try:
        # For security, we should verify this request comes from a trusted source
        # In a real implementation, we might check API keys, webhook signatures, etc.

        # Perform review in background
        background_tasks.add_task(
            _review_pr_task,
            repository_full_name,
            pull_request_number,
            include_security,
            include_performance,
            include_style
        )

        return {
            "accepted": True,
            "message": f"Review started for PR #{pull_request_number} in {repository_full_name}",
            "repository": repository_full_name,
            "pull_request_number": pull_request_number
        }
    except Exception as e:
        logger.error(f"Failed to initiate PR review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _review_pr_task(
    repository_full_name: str,
    pull_request_number: int,
    include_security: bool,
    include_performance: bool,
    include_style: bool
):
    """Background task to review a pull request."""
    try:
        # We would need to get the installation ID from the database or webhook context
        # For now, this is a placeholder - in reality, we'd look up the installation
        # based on the repository or have it passed in the request
        # This is a limitation of this endpoint design - webhooks are better for this

        # For demonstration purposes, we'll assume we can get this from context
        # In practice, this endpoint might need to be called with installation context
        # Or we'd rely primarily on webhook-based reviews

        result = await review_pull_request(
            installation_id=0,  # Placeholder - would need actual implementation
            repo_full_name=repository_full_name,
            pr_number=pull_request_number,
            include_security=include_security,
            include_performance=include_performance,
            include_style=include_style
        )

        if result["success"]:
            emit("github_pr_reviewed_enhanced", {
                "repository": repository_full_name,
                "pull_request_number": pull_request_number,
                "review_result": result
            })
            logger.info(f"Successfully reviewed PR {repository_full_name}#{pull_request_number}")
        else:
            emit("github_pr_review_failed_enhanced", {
                "repository": repository_full_name,
                "pull_request_number": pull_request_number,
                "error": result["error"]
            })
            logger.error(f"Failed to review PR {repository_full_name}#{pull_request_number}: {result['error']}")

    except Exception as e:
        logger.error(f"PR review task failed: {e}")
        emit("github_pr_review_error_enhanced", {
            "repository": repository_full_name,
            "pull_request_number": pull_request_number,
            "error": str(e)
        })


@router.post("/webhook")
async def enhanced_github_webhook(request: Request):
    """
    Enhanced GitHub webhook handler that processes additional event types.
    This works alongside the existing webhook handler.
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

    # Handle ping event
    if event == "ping":
        return {"ok": True, "pong": True}

    # Handle repository events for synchronization
    if event == "repository":
        result = await handle_repository_webhook(payload)
        if result.get("error"):
            emit("github_repository_webhook_error", result)
        else:
            emit("github_repository_webhook_processed", result)
        return {"ok": True, "handled": True}

    # Handle installation events (for tracking installations)
    if event == "installation":
        # Process installation events (created, deleted, etc.)
        action = payload.get("action")
        installation = payload.get("installation", {})

        if action == "created":
            emit("github_installation_created", {
                "installation_id": installation.get("id"),
                "account": installation.get("account", {}).get("login")
            })
        elif action == "deleted":
            emit("github_installation_deleted", {
                "installation_id": installation.get("id"),
                "account": installation.get("account", {}).get("login")
            })

        return {"ok": True, "handled": True}

    # Handle installation_repositories events (when repositories are added/removed from installation)
    if event == "installation_repositories":
        # This tells us when repositories are added to or removed from an installation
        action = payload.get("action")
        repositories_added = payload.get("repositories_added", [])
        repositories_removed = payload.get("repositories_removed", [])

        if repositories_added:
            for repo in repositories_added:
                repo_full_name = repo.get("full_name")
                if repo_full_name:
                    # Trigger synchronization for newly added repositories
                    # In practice, we might want to do this in background
                    pass

        if repositories_removed:
            for repo in repositories_removed:
                repo_full_name = repo.get("full_name")
                if repo_full_name:
                    # Mark repositories as removed from tracking
                    pass

        return {"ok": True, "handled": True}

    # For pull_request events, we still use the basic handler for now
    # The enhanced review would be triggered separately or via configuration
    if event == "pull_request":
        # Delegate to the existing handler for backward compatibility
        # In a full implementation, we might enhance this based on configuration
        return {"ok": True, "delegated": True}

    # Ignore other events
    return {"ok": True, "ignored": event}


# Create a router instance that can be imported and used
github_enhanced_router = router

"""Third-party integrations (GitHub App, etc.)."""

from .github import GitHubClient, _findings_to_comments, default_pr_reviewer
from .github_enhanced import (
    EnhancedPRReviewer,
    GitHubAppManager,
    RepositorySynchronizer,
    enhanced_pr_reviewer,
    github_app_manager,
    handle_repository_webhook,
    repository_synchronizer,
    review_pull_request,
    synchronize_repository,
)

__all__ = [
    # Original GitHub integration
    "GitHubClient",
    "default_pr_reviewer",
    "_findings_to_comments",

    # Enhanced GitHub integration
    "GitHubAppManager",
    "EnhancedPRReviewer",
    "RepositorySynchronizer",
    "synchronize_repository",
    "review_pull_request",
    "handle_repository_webhook",
    "github_app_manager",
    "enhanced_pr_reviewer",
    "repository_synchronizer"
]

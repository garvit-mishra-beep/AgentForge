"""Third-party integrations (GitHub App, etc.)."""

from .github import (
    GitHubClient,
    default_pr_reviewer,
    _findings_to_comments
)

from .github_enhanced import (
    GitHubAppManager,
    EnhancedPRReviewer,
    RepositorySynchronizer,
    synchronize_repository,
    review_pull_request,
    handle_repository_webhook,
    github_app_manager,
    enhanced_pr_reviewer,
    repository_synchronizer
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
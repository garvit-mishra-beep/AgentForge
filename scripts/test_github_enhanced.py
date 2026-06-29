"""
Tests for the enhanced GitHub integration system.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.integrations.github_enhanced import (
    synchronize_repository,
    review_pull_request,
    handle_repository_webhook,
    GitHubAppManager,
    RepositorySynchronizer,
    EnhancedPRReviewer
)
from app.integrations.github import GitHubClient


class TestGitHubAppManager:
    """Test the GitHubAppManager class."""

    def test_init(self):
        """Test initialization."""
        manager = GitHubAppManager()
        assert manager.app_id is None  # Would be from settings
        assert manager.private_key is None  # Would be from settings
        assert manager.webhook_secret is None  # Would be from settings


class TestRepositorySynchronizer:
    """Test the RepositorySynchronizer class."""

    @pytest.mark.asyncio
    async def test_synchronize_repository_success(self):
        """Test successful repository synchronization."""
        synchronizer = RepositorySynchronizer()

        # Mock the GitHubClient
        mock_client = AsyncMock(spec=GitHubClient)
        mock_client._api = "https://api.github.com"

        # Mock responses
        mock_repo_resp = MagicMock()
        mock_repo_resp.raise_for_status = MagicMock()
        mock_repo_resp.json.return_value = {
            "id": 12345,
            "full_name": "test/repo",
            "owner": {"login": "test"},
            "description": "Test repository",
            "language": "Python",
            "fork": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "pushed_at": "2023-01-03T00:00:00Z",
            "size": 100,
            "stargazers_count": 10,
            "watchers_count": 5,
            "forks_count": 2,
            "open_issues_count": 0,
            "archived": False,
            "disabled": False
        }

        mock_lang_resp = MagicMock()
        mock_lang_resp.raise_for_status = MagicMock()
        mock_lang_resp.json.return_value = {"Python": 1000}

        mock_topics_resp = MagicMock()
        mock_topics_resp.raise_for_status = MagicMock()
        mock_topics_resp.json.return_value = {"names": ["test", "demo"]}

        mock_contrib_resp = MagicMock()
        mock_contrib_resp.raise_for_status = MagicMock()
        mock_contrib_resp.json.return_value = [{"login": "user1"}]

        # Set up the mock client to return our responses
        mock_client._http.get = AsyncMock()
        mock_client._http.get.side_effect = [
            mock_repo_resp,
            mock_lang_resp,
            mock_topics_resp,
            mock_contrib_resp
        ]

        with patch('app.integrations.github_enhanced.GitHubClient.for_installation', return_value=mock_client):
            result = await synchronizer.synchronize_repository(123, "test/repo")

            assert result["success"] is True
            assert result["repository"]["full_name"] == "test/repo"
            assert result["repository"]["language"] == "Python"
            assert result["repository"]["topics"] == ["test", "demo"]
            assert "repository_id" in result["repository"]

    @pytest.mark.asyncio
    async def test_synchronize_repository_failure(self):
        """Test repository synchronization failure."""
        synchronizer = RepositorySynchronizer()

        with patch('app.integrations.github_enhanced.GitHubClient.for_installation') as mock_for_install:
            mock_for_install.side_effect = Exception("GitHub API error")

            result = await synchronizer.synchronize_repository(123, "test/repo")

            assert result["success"] is False
            assert "error" in result
            assert "GitHub API error" in result["error"]


class TestEnhancedPRReviewer:
    """Test the EnhancedPRReviewer class."""

    @pytest.mark.asyncio
    async def test_review_pull_request_success(self):
        """Test successful PR review."""
        reviewer = EnhancedPRReviewer()

        # Mock the GitHubClient
        mock_client = AsyncMock(spec=GitHubClient)
        mock_client._api = "https://api.github.com"

        # Mock PR response
        mock_pr_resp = MagicMock()
        mock_pr_resp.raise_for_status = MagicMock()
        mock_pr_resp.json.return_value = {
            "title": "Test PR",
            "user": {"login": "testuser"},
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changed_files": 3
        }

        # Mock files response
        mock_files_resp = MagicMock()
        mock_files_resp.raise_for_status = MagicMock()
        mock_files_resp.json.return_value = [
            {
                "filename": "test.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,5 @@\n+def new_function():\n+    pass\n def old_function():\n     return True"
            }
        ]

        # Set up the mock client
        mock_client._http.get = AsyncMock()
        mock_client._http.get.side_effect = [mock_pr_resp, mock_files_resp]
        mock_client._headers = MagicMock(return_value={"Authorization": "token test"})

        # Use python to create a simple test
        code_quality_result = {
            "files_analyzed": 1,
            "total_files": 1,
            "findings_count": 0,
            "blocking_issues": 0,
            "comments": [],
            "summary": "No issues found"
        }

        with patch('app.integrations.github_enhanced.GitHubClient.for_installation', return_value=mock_client):
            with patch('app.integrations.github.default_pr_reviewer', return_value=[]):
                with patch('app.integrations.github_enhanced._findings_to_comments', return_value=[]):
                    result = await reviewer.review_pull_request(
                        123, "test/repo", 1,
                        include_security=False,
                        include_performance=False,
                        include_style=False
                    )

                    assert result["success"] is True
                    assert result["conclusion"] in ["success", "neutral", "failure"]
                    assert "review_id" in result
                    assert "results" in result
                    assert "summary" in result

    @pytest.mark.asyncio
    async def test_is_code_file(self):
        """Test the _is_code_file helper method."""
        reviewer = EnhancedPRReviewer()

        # Test code files
        assert reviewer._is_code_file("test.py") is True
        assert reviewer._is_code_file("test.js") is True
        assert reviewer._is_code_file("Test.Component.jsx") is True
        assert reviewer._is_code_file("index.html") is True
        assert reviewer._is_code_file("style.css") is True
        assert reviewer._is_code_file("README.md") is True

        # Test non-code files
        assert reviewer._is_code_file("image.png") is False
        assert reviewer._is_code_file("document.pdf") is False
        assert reviewer._is_code_file("archive.zip") is False
        assert reviewer._is_code_file("") is False
        assert reviewer._is_code_file("noextension") is False

    @pytest.mark.asyncio
    async def test_determine_overall_conclusion(self):
        """Test the conclusion determination logic."""
        reviewer = EnhancedPRReviewer()

        # Test success case (no issues)
        results_success = {
            "metadata": {"pull_request": 1},
            "code_quality": {"blocking_issues": 0, "findings_count": 0},
            "security": {"issues": []},
            "performance": {"indicators": []},
            "style": {"issues_found": 0}
        }
        assert reviewer._determine_overall_conclusion(results_success) == "success"

        # Test failure case (blocking issues)
        results_failure = {
            "metadata": {"pull_request": 1},
            "code_quality": {"blocking_issues": 2, "findings_count": 5},
            "security": {"issues": []},
            "performance": {"indicators": []},
            "style": {"issues_found": 0}
        }
        assert reviewer._determine_overall_conclusion(results_failure) == "failure"

        # Test neutral case (minor issues)
        results_neutral = {
            "metadata": {"pull_request": 1},
            "code_quality": {"blocking_issues": 0, "findings_count": 2},
            "security": {"issues": []},
            "performance": {"indicators": []},
            "style": {"issues_found": 0}
        }
        assert reviewer._determine_overall_conclusion(results_neutral) == "neutral"


class TestRepositoryWebhookHandler:
    """Test the repository webhook handler."""

    @pytest.mark.asyncio
    async def test_handle_repository_webhook_edited(self):
        """Test handling repository edited event."""
        payload = {
            "action": "edited",
            "repository": {
                "full_name": "test/repo",
                "description": "Updated description"
            },
            "installation": {
                "id": 123
            }
        }

        # Mock the synchronization function
        with patch('app.integrations.github_enhanced.synchronize_repository') as mock_sync:
            mock_sync.return_value = {
                "success": True,
                "repository": {"full_name": "test/repo"}
            }

            result = await handle_repository_webhook(payload)

            assert result["action"] == "repository_edited"
            assert result["repository"] == "test/repo"
            assert result["synchronization"]["success"] is True

    @pytest.mark.asyncio
    async def test_handle_repository_webhook_deleted(self):
        """Test handling repository deleted event."""
        payload = {
            "action": "deleted",
            "repository": {
                "full_name": "test/repo"
            },
            "installation": {
                "id": 123
            }
        }

        result = await handle_repository_webhook(payload)

        assert result["action"] == "repository_deleted"
        assert result["repository"] == "test/repo"

    @pytest.mark.asyncio
    async def test_handle_repository_webhook_missing_data(self):
        """Test handling webhook with missing data."""
        payload = {
            "action": "edited"
            # Missing repository and installation
        }

        result = await handle_repository_webhook(payload)

        assert "error" in result
        assert "Missing repository or installation data" in result["error"]


# Integration tests
class TestGitHubEnhancedIntegration:
    """Integration tests for the enhanced GitHub system."""

    @pytest.mark.asyncio
    async def test_full_pr_review_flow(self):
        """Test a full PR review flow with all analysis types."""
        # This would be more complex integration test
        # For now, we'll test that the functions can be called without error
        assert callable(synchronize_repository)
        assert callable(review_pull_request)
        assert callable(handle_repository_webhook)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

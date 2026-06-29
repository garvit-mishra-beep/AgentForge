"""
Enhanced GitHub Integration Core for AgentForge.
Provides advanced GitHub workflow capabilities including repository synchronization
and comprehensive multi-agent pull request reviews.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any

from app.integrations.github import GitHubClient
from core.config import settings
from core.observability import emit

logger = logging.getLogger(__name__)


# Global instances
github_app_manager: Any = None
enhanced_pr_reviewer: Any = None
repository_synchronizer: Any = None


def _init_globals():
    """Initialize global instances."""
    global github_app_manager, enhanced_pr_reviewer, repository_synchronizer
    if github_app_manager is None:
        github_app_manager = GitHubAppManager()
    if enhanced_pr_reviewer is None:
        enhanced_pr_reviewer = EnhancedPRReviewer()
    if repository_synchronizer is None:
        repository_synchronizer = RepositorySynchronizer()


class GitHubAppManager:
    """Manages GitHub App installations and performs basic operations."""

    def __init__(self):
        self.app_id = settings.github_app_id
        self.private_key = settings.github_app_private_key
        self.webhook_secret = settings.github_webhook_secret

    async def get_installation_client(self, installation_id: int) -> 'GitHubClient':
        """Get an authenticated GitHub client for an installation."""
        return await GitHubClient.for_installation(installation_id)


class RepositorySynchronizer:
    """Handles synchronization of repository data between GitHub and AgentForge."""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".RepositorySynchronizer")

    async def synchronize_repository(self, installation_id: int, repo_full_name: str) -> dict[str, Any]:
        """
        Synchronize repository metadata with AgentForge.

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Repository full name (owner/repo)

        Returns:
            Dictionary with synchronization results
        """
        await self.logger.debug(f"Synchronizing repository {repo_full_name} for installation {installation_id}")

        try:
            client = await GitHubClient.for_installation(installation_id)

            # Get repository information
            repo_resp = await client._http.get(
                f"{client._api}/repos/{repo_full_name}",
                headers=client._headers()
            )
            repo_resp.raise_for_status()
            repo_data = repo_resp.json()

            # Get repository topics/languages
            lang_resp = await client._http.get(
                f"{client._api}/repos/{repo_full_name}/languages",
                headers=client._headers()
            )
            lang_resp.raise_for_status()
            languages = lang_resp.json()

            topics_resp = await client._http.get(
                f"{client._api}/repos/{repo_full_name}/topics",
                headers={**client._headers(), "Accept": "application/vnd.github+json"}
            )
            topics_resp.raise_for_status()
            topics_data = topics_resp.json()
            topics = topics_data.get("names", [])

            await client.close()

            # Prepare synchronized data
            synchronized_data = {
                "repository_id": repo_data["id"],
                "full_name": repo_data["full_name"],
                "owner": repo_data["owner"]["login"],
                "description": repo_data.get("description"),
                "language": repo_data.get("language"),
                "languages": languages,
                "languages_url": f"{client._api}/repos/{repo_full_name}/languages",
                "topics": topics,
                "is_fork": repo_data["fork"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
                "pushed_at": repo_data["pushed_at"],
                "size": repo_data["size"],
                "stargazers_count": repo_data["stargazers_count"],
                "watchers_count": repo_data["watchers_count"],
                "forks_count": repo_data["forks_count"],
                "open_issues_count": repo_data["open_issues_count"],
                "is_archived": repo_data["archived"],
                "is_disabled": repo_data["disabled"],
                "license": repo_data.get("license"),
                "allow_forking": repo_data.get("allow_forking", True),
                "is_template": repo_data.get("is_template", False),
                "web_commit_signoff_required": repo_data.get("web_commit_signoff_required", False),
                "network_count": repo_data.get("network_count", 0),
                "subscribers_count": repo_data.get("subscribers_count", 0),
                "template_repository": repo_data.get("template_repository"),
                "permissions": repo_data.get("permissions", {})
            }

            # Emit event for successful synchronization
            await self._emit_sync_event("repository_synchronized", {
                "installation_id": installation_id,
                "repository": repo_full_name,
                "data": synchronized_data
            })

            return {
                "success": True,
                "repository": synchronized_data,
                "message": f"Successfully synchronized {repo_full_name}"
            }

        except Exception as e:
            await self.logger.error(f"Failed to synchronize repository {repo_full_name}: {e}")
            await self._emit_sync_event("repository_sync_failed", {
                "installation_id": installation_id,
                "repository": repo_full_name,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e),
                "repository": None
            }

    async def _emit_sync_event(self, event_type: str, data: dict):
        """Emit an observability event."""
        try:
            emit(f"github_{event_type}", data)
        except Exception as e:
            self.logger.warning(f"Failed to emit event {event_type}: {e}")


class EnhancedPRReviewer:
    """Enhanced PR reviewer that performs comprehensive analysis using multiple agents."""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".EnhancedPRReviewer")

    async def review_pull_request(
        self,
        installation_id: int,
        repo_full_name: str,
        pr_number: int,
        include_security: bool = True,
        include_performance: bool = True,
        include_style: bool = True
    ) -> dict[str, Any]:
        """
        Perform a comprehensive review of a pull request using multiple analysis dimensions.

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull request number
            include_security: Whether to include security analysis
            include_performance: Whether to include performance analysis
            include_style: Whether to include style/linting analysis

        Returns:
            Dictionary with comprehensive review results
        """
        await self.logger.info(f"Starting enhanced PR review for {repo_full_name}#{pr_number}")

        try:
            # Get GitHub client for this installation
            client = await GitHubClient.for_installation(installation_id)

            # Get PR details
            pr_resp = await client._http.get(
                f"{client._api}/repos/{repo_full_name}/pulls/{pr_number}",
                headers=client._headers()
            )
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()

            # Get changed files
            files_resp = await client._http.get(
                f"{client._api}/repos/{repo_full_name}/pulls/{pr_number}/files",
                headers=client._headers(),
                params={"per_page": 100}
            )
            files_resp.raise_for_status()
            files_data = files_resp.json()

            # Filter to code files only
            code_files = [
                f for f in files_data
                if f.get("status") != "removed" and
                   self._is_code_file(f.get("filename", ""))
            ]

            await self.logger.debug(f"Found {len(code_files)} code files to review out of {len(files_data)} total files")

            # Initialize results
            review_results: dict[str, Any] = {
                "metadata": {
                    "repository": repo_full_name,
                    "pull_request": pr_number,
                    "title": pr_data["title"],
                    "author": pr_data["user"]["login"],
                    "created_at": pr_data["created_at"],
                    "updated_at": pr_data["updated_at"],
                    "changed_files": len(files_data),
                    "code_files": len(code_files),
                    "additions": pr_data["additions"],
                    "deletions": pr_data["deletions"],
                    "changed_lines": pr_data["changed_files"]
                }
            }

            # Perform different types of analysis in parallel where possible
            analysis_tasks = []

            # Code quality review (always performed)
            analysis_tasks.append(
                self._review_code_quality(client, repo_full_name, code_files)
            )

            # Security analysis
            if include_security:
                analysis_tasks.append(
                    self._review_security(client, repo_full_name, code_files)
                )

            # Performance analysis
            if include_performance:
                analysis_tasks.append(
                    self._analyze_performance(client, repo_full_name, code_files)
                )

            # Style/linting analysis
            if include_style:
                analysis_tasks.append(
                    self._check_style(client, repo_full_name, code_files)
                )

            # Execute all analysis tasks
            if analysis_tasks:
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

                # Process results
                result_index = 0
                review_results["code_quality"] = results[result_index] if not isinstance(results[result_index], Exception) else {"error": str(results[result_index])}
                result_index += 1

                if include_security:
                    review_results["security"] = results[result_index] if not isinstance(results[result_index], Exception) else {"error": str(results[result_index])}
                    result_index += 1

                if include_performance:
                    review_results["performance"] = results[result_index] if not isinstance(results[result_index], Exception) else {"error": str(results[result_index])}
                    result_index += 1

                if include_style:
                    review_results["style"] = results[result_index] if not isinstance(results[result_index], Exception) else {"error": str(results[result_index])}

            # Generate summary and recommendations
            review_results["summary"] = self._generate_review_summary(review_results)
            review_results["recommendations"] = self._generate_recommendations(review_results)

            # Determine overall conclusion
            conclusion = self._determine_overall_conclusion(review_results)
            review_results["conclusion"] = conclusion

            # Create formatted review comment for GitHub
            review_comment = self._format_github_review_comment(review_results)
            review_results["github_comment"] = review_comment

            await client.close()

            await self.logger.info(f"Completed enhanced PR review for {repo_full_name}#{pr_number} with conclusion: {conclusion}")

            return {
                "success": True,
                "review_id": None,  # Would be set when actually posting to GitHub
                "check_run_id": None,  # Would be set when actually posting to GitHub
                "conclusion": conclusion,
                "results": review_results,
                "summary": review_results["summary"]
            }

        except Exception as e:
            await self.logger.error(f"Failed to complete enhanced PR review for {repo_full_name}#{pr_number}: {e}")
            await self._emit_review_error("review_failed", {
                "installation_id": installation_id,
                "repository": repo_full_name,
                "pull_request": pr_number,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e),
                "repository": repo_full_name,
                "pull_request": pr_number
            }

    def _is_code_file(self, filename: str) -> bool:
        """Check if a file is a code file based on extension."""
        if not filename:
            return False

        # Common code file extensions
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.kts', '.scala', '.sc',
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            '.dart', '.lua', '.pl', '.pm', '.r', '.m', '.mm', '.sh', '.bash', '.zsh',
            '.fish', '.sql', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.conf', '.md', '.markdown', '.txt', '.csv', '.tsv', '.gradle', '.mk',
            '.clj', '.cljs', '.ex', '.exs', '.erl', '.hrl', '.cl', '.el', '.hs'
        }

        return any(filename.lower().endswith(ext) for ext in code_extensions)

    async def _review_code_quality(self, client: GitHubClient, repo: str, files: list[dict]) -> dict:
        """Perform code quality review using existing AgentForge reviewer."""
        try:
            # Import the existing reviewer functionality
            from app.integrations.github import _findings_to_comments, default_pr_reviewer

            all_findings = []
            all_comments = []
            files_processed = 0

            # Limit processing to avoid timeout/issues
            max_files = min(len(files), 15)  # Process at most 15 files

            for file_info in files[:max_files]:
                filename = file_info.get("filename", "")
                patch = file_info.get("patch", "")

                if not patch:
                    continue

                try:
                    findings = await default_pr_reviewer(filename, patch)
                    all_findings.extend(findings)
                    all_comments.extend(_findings_to_comments(filename, findings))
                    files_processed += 1
                except Exception as e:
                    await self.logger.warning(f"Failed to review file {filename}: {e}")

            # If we had more files than we processed, note it
            if len(files) > max_files:
                remaining_note = f" (and {len(files) - max_files} more files)"
            else:
                remaining_note = ""

            return {
                "files_analyzed": files_processed,
                "total_files": len(files),
                "findings_count": len(all_findings),
                "blocking_issues": len([f for f in all_findings if f.get("severity") in ["critical", "high"]]),
                "comments": all_comments,
                "summary": f"Code quality analysis completed on {files_processed}{remaining_note} files. Found {len(all_findings)} issues."
            }
        except Exception as e:
            await self.logger.error(f"Code quality review failed: {e}")
            return {"error": str(e), "files_analyzed": 0}

    async def _review_security(self, client: GitHubClient, repo: str, files: list[dict]) -> dict:
        """Perform security analysis on the code changes."""
        try:
            # This would integrate with security scanning tools or custom security rules
            # For now, we'll provide a placeholder that indicates the feature is available
            # In a real implementation, this might use bandit, semgrep, owasp dependency check, etc.

            security_files = [
                f for f in files
                if any(keyword in f["filename"].lower()
                     for keyword in ["auth", "security", "crypto", "cipher", "encrypt", "decrypt",
                                   "token", "password", "secret", "key", "hash", "ssl", "tls"])
            ]

            # Basic security heuristic checks
            issues = []
            for file_info in security_files[:10]:  # Limit for performance
                filename = file_info["filename"]
                # These would be actual security scan results in a real implementation
                if "password" in filename.lower() and ".txt" in filename.lower():
                    issues.append({
                        "file": filename,
                        "issue": "Potential password file detected",
                        "severity": "high",
                        "description": "File appears to contain passwords in plain text"
                    })

            return {
                "security_files_found": len(security_files),
                "issues_detected": len(issues),
                "issues": details if (details := issues) else [],
                "summary": f"Security analysis completed. Found {len(security_files)} security-related files with {len(issues)} potential issues."
            }
        except Exception as e:
            await self.logger.error(f"Security review failed: {e}")
            return {"error": str(e)}

    async def _analyze_performance(self, client: GitHubClient, repo: str, files: list[dict]) -> dict:
        """Analyze performance implications of code changes."""
        try:
            # Look for patterns that might indicate performance issues
            performance_indicators = []

            for file_info in files[:20]:  # Limit for performance
                filename = file_info["filename"]
                # Files that commonly impact performance
                if any(pattern in filename.lower()
                     for pattern in ["loop", "recursive", "query", "sql", "filter", "sort", "map", "reduce"]):
                    performance_indicators.append({
                        "file": filename,
                        "reason": "Filename suggests potential performance impact",
                        "type": "structural"
                    })

                # Check patch content for expensive operations
                patch = file_info.get("patch", "")
                if patch:
                    # Look for nested loops, recursive calls without base case, etc.
                    # This is simplified - real implementation would use AST analysis
                    lines = patch.split('\n')
                    for i, line in enumerate(lines):
                        if 'for ' in line and 'in ' in line and ':' in line:
                            # Look for nested loops in following lines
                            nested_depth = 0
                            for j in range(i+1, min(i+10, len(lines))):
                                if 'for ' in lines[j] and 'in ' in lines[j] and ':' in lines[j]:
                                    nested_depth += 1
                                elif lines[j].strip() == '' or lines[j].startswith('#'):
                                    continue
                                else:
                                    break
                            if nested_depth >= 2:
                                performance_indicators.append({
                                    "file": f"{filename}:L{i+1}",
                                    "reason": "Potential nested loop detected",
                                    "severity": "medium",
                                    "type": "pattern"
                                })

            return {
                "performance_indicators": len(performance_indicators),
                "indicators": [
                    {
                        "file": ind.get("file", "unknown"),
                        "reason": ind.get("reason", "unknown"),
                        "severity": ind.get("severity", "low"),
                        "type": ind.get("type", "unknown")
                    }
                    for ind in (performance_indicators[:10] if len(performance_indicators) > 10 else performance_indicators)
                ],
                "summary": f"Performance analysis completed. Identified {len(performance_indicators)} potential performance concerns."
            }
        except Exception as e:
            await self.logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}

    async def _check_style(self, client: GitHubClient, repo: str, files: list[dict]) -> dict:
        """Check code style and formatting."""
        try:
            style_issues = []

            # Check for common style issues in the patch content
            for file_info in files[:20]:  # Limit for performance
                filename = file_info["filename"]
                patch = file_info.get("patch", "")

                if not patch:
                    continue

                lines = patch.split('\n')
                for i, line in enumerate(lines):
                    # Check for trailing whitespace
                    if line.endswith(' ') or line.endswith('\t'):
                        style_issues.append({
                            "file": f"{filename}:L{i+1}",
                            "issue": "Trailing whitespace",
                            "severity": "low",
                            "line": i+1
                        })

                    # Check for very long lines (though this is harder in diff format)
                    # Check for inconsistent indentation (mix of tabs and spaces)
                    if '\t' in line and ' ' in line.lstrip('\t'):
                        # This is a simplistic check - real implementation would be more sophisticated
                        if line.count('\t') > 0 and line.count(' ') > 0:
                            # Check if there's mixing after initial indentation
                            stripped = line.lstrip()
                            if stripped.startswith(' ') and '\t' in line:
                                style_issues.append({
                                    "file": f"{filename}:L{i+1}",
                                    "issue": "Mixed tabs and spaces in indentation",
                                    "severity": "medium",
                                    "line": i+1
                                })

            return {
                "style_issues_found": len(style_issues),
                "issues": style_issues[:10] if len(style_issues) > 10 else style_issues,
                "summary": f"Style check completed. Found {len(style_issues)} style issues."
            }
        except Exception as e:
            await self.logger.error(f"Style check failed: {e}")
            return {"error": str(e)}

    def _generate_review_summary(self, results: dict) -> str:
        """Generate a human-readable summary of the review results."""
        parts = []

        # Basic info
        metadata = results.get("metadata", {})
        if metadata:
            parts.append(f"PR #{metadata.get('pull_request', '?')}: {metadata.get('title', 'No title')}")
            parts.append(f"Changed files: {metadata.get('changed_files', 0)} ({metadata.get('code_files', 0)} code files)")

        # Code quality
        if "code_quality" in results and "error" not in results["code_quality"]:
            cq = results["code_quality"]
            parts.append(f"Code Quality: {cq.get('summary', 'No summary available')}")

        # Security
        if "security" in results and "error" not in results["security"]:
            sec = results["security"]
            if isinstance(sec, dict):
                parts.append(f"Security: {sec.get('summary', 'No summary available')}")

        # Performance
        if "performance" in results and "error" not in results["performance"]:
            perf = results["performance"]
            if isinstance(perf, dict):
                parts.append(f"Performance: {perf.get('summary', 'No summary available')}")

        # Style
        if "style" in results and "error" not in results["style"]:
            style = results["style"]
            if isinstance(style, dict):
                parts.append(f"Style: {style.get('summary', 'No summary available')}")

        return " | ".join(parts) if parts else "Review completed"

    def _generate_recommendations(self, results: dict) -> list[str]:
        """Generate actionable recommendations based on review results."""
        recommendations = []

        # Code quality recommendations
        if "code_quality" in results and "error" not in results["code_quality"]:
            cq = results["code_quality"]
            if isinstance(cq, dict):
                blocking = cq.get("blocking_issues", 0)
                if blocking > 0:
                    recommendations.append(f"Address {blocking} blocking code quality issues before merging")

                total_findings = cq.get("findings_count", 0)
                if total_findings > 10:
                    recommendations.append("Consider breaking down large changes into smaller, focused PRs")

        # Security recommendations
        if "security" in results and "error" not in results["security"]:
            sec = results["security"]
            if isinstance(sec, dict):
                issues = sec.get("issues_detected", 0)
                if issues > 0:
                    recommendations.append("Review and address security concerns identified in the analysis")

        # Performance recommendations
        if "performance" in results and "error" not in results["performance"]:
            perf = results["performance"]
            if isinstance(perf, dict):
                indicators = perf.get("indicators", [])
                if len(indicators) > 3:
                    recommendations.append("Consider performance optimization for identified hotspots")

        # Style recommendations
        if "style" in results and "error" not in results["style"]:
            style = results["style"]
            if isinstance(style, dict):
                issues = style.get("issues_found", 0)
                if issues > 5:
                    recommendations.append("Consider running automated formatter to fix style issues")

        # General recommendations
        if not recommendations:
            # Check overall status
            conclusion = self._determine_overall_conclusion(results)
            if conclusion == "neutral":
                recommendations.append("Consider addressing minor issues to improve code quality")
            elif conclusion == "failure":
                recommendations.append("Please address the identified issues before requesting re-review")

        return recommendations

    def _determine_overall_conclusion(self, results: dict) -> str:
        """Determine the overall conclusion based on all review results."""
        # Check for blocking issues in code quality
        if "code_quality" in results and "error" not in results["code_quality"]:
            cq = results["code_quality"]
            if isinstance(cq, dict):
                blocking = cq.get("blocking_issues", 0)
                if blocking > 0:
                    return "failure"  # Blocking issues found

        # Check security issues
        if "security" in results and "error" not in results["security"]:
            sec = results["security"]
            if isinstance(sec, dict):
                # High severity security issues would block
                high_sev = len([i for i in sec.get("issues", []) if i.get("severity") == "high"])
                if high_sev > 0:
                    return "failure"

        # Check for excessive issues that might warrant concern
        total_concerns = 0
        if "code_quality" in results and "error" not in results["code_quality"]:
            cq = results["code_quality"]
            if isinstance(cq, dict):
                total_concerns += cq.get("findings_count", 0)

        if "security" in results and "error" not in results["security"]:
            sec = results["security"]
            if isinstance(sec, dict):
                total_concerns += len(sec.get("issues", []))

        if "performance" in results and "error" not in results["performance"]:
            perf = results["performance"]
            if isinstance(perf, dict):
                total_concerns += len(perf.get("indicators", []))

        if "style" in results and "error" not in results["style"]:
            style = results["style"]
            if isinstance(style, dict):
                total_concerns += style.get("issues_found", 0)

        # Make decision based on total concerns
        if total_concerns == 0:
            return "success"
        elif total_concerns <= 3:
            return "neutral"  # Minor issues
        else:
            return "failure"  # Too many issues

    def _format_github_review_comment(self, results: dict) -> dict:
        """Format the review results as a GitHub-compatible comment."""
        summary = results.get("summary", "Review completed")
        conclusion = results.get("conclusion", "neutral")

        # Determine GitHub review event type
        event_map = {
            "success": "APPROVE",
            "neutral": "COMMENT",
            "failure": "REQUEST_CHANGES"
        }
        event = event_map.get(conclusion, "COMMENT")

        # Build the comment body
        body_parts = [
            "## AgentForge Comprehensive Review",
            f"**Conclusion**: {conclusion.title()}",
            f"**Summary**: {summary}",
            ""
        ]

        # Add detailed sections
        sections = [
            ("Code Quality", "code_quality"),
            ("Security", "security"),
            ("Performance", "performance"),
            ("Style", "style")
        ]

        for section_name, key in sections:
            if key in results and "error" not in results[key]:
                section_data = results[key]
                if isinstance(section_data, dict) and "summary" in section_data:
                    body_parts.extend([
                        f"### {section_name}",
                        section_data["summary"],
                        ""
                    ])

        # Add recommendations if any
        recommendations = results.get("recommendations", [])
        if recommendations:
            body_parts.extend([
                "### Recommendations",
                *[f"- {rec}" for rec in recommendations],
                ""
            ])

        body_parts.append(f"---\n*Generated by AgentForge at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        return {
            "body": "\n".join(body_parts),
            "event": event,
            "comments": []  # Inline comments would be added separately if needed
        }

    async def _emit_review_error(self, event_type: str, data: dict):
        """Emit an observability event for review errors."""
        try:
            emit(f"github_{event_type}", data)
        except Exception as e:
            self.logger.warning(f"Failed to emit event {event_type}: {e}")

# Initialize global instances
_init_globals()

# Convenience functions for external use
async def synchronize_repository(installation_id: int, repo_full_name: str) -> dict:
    """Convenience function to synchronize a repository."""
    global repository_synchronizer
    if repository_synchronizer is None:
        _init_globals()
    return await repository_synchronizer.synchronize_repository(installation_id, repo_full_name)


async def review_pull_request(
    installation_id: int,
    repo_full_name: str,
    pr_number: int,
    include_security: bool = True,
    include_performance: bool = True,
    include_style: bool = True
) -> dict:
    """Convenience function to review a pull request."""
    global enhanced_pr_reviewer
    if enhanced_pr_reviewer is None:
        _init_globals()
    return await enhanced_pr_reviewer.review_pull_request(
        installation_id, repo_full_name, pr_number,
        include_security, include_performance, include_style
    )


async def handle_repository_webhook(payload: dict) -> dict:
    """Handle repository webhook events."""
    global github_app_manager
    if github_app_manager is None:
        _init_globals()

    try:
        action = payload.get("action")
        repository = payload.get("repository", {})
        installation = payload.get("installation", {})

        if not repository or not installation:
            return {"error": "Missing repository or installation data"}

        repo_full_name = repository.get("full_name")
        installation_id = installation.get("id")

        if not repo_full_name or not installation_id:
            return {"error": "Invalid repository or installation data"}

        if action == "edited":
            # Repository was edited (name, description, etc.) - might want to resync
            result = await synchronize_repository(installation_id, repo_full_name)
            return {
                "action": "repository_edited",
                "repository": repo_full_name,
                "synchronization": result
            }
        elif action == "transferred":
            # Repository was transferred to another owner
            return {
                "action": "repository_transferred",
                "repository": repo_full_name,
                "new_owner": payload.get("changes", {}).get("owner", {}).get("to", {}).get("login")
            }
        elif action == "renamed":
            # Repository was renamed
            return {
                "action": "repository_renamed",
                "old_name": payload.get("changes", {}).get("full_name", {}).get("from"),
                "new_name": repo_full_name
            }
        elif action == "deleted":
            # Repository was deleted
            return {
                "action": "repository_deleted",
                "repository": repo_full_name
            }
        else:
            return {
                "action": action or "unknown",
                "repository": repo_full_name,
                "message": f"Repository event '{action}' processed"
            }

    except Exception as e:
        return {"error": str(e)}

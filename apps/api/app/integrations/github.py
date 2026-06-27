"""GitHub App integration — PR review bot.

Implements the full GitHub App auth flow:

  1. Sign a short-lived **app JWT** with the app's RSA private key (RS256).
  2. Exchange it for an **installation access token** scoped to one install.
  3. Use that token to read the PR's changed files and post a review + check run.

Inbound webhooks are authenticated with an HMAC-SHA256 signature
(``X-Hub-Signature-256``) over the raw request body.

The heavy lifting (auth, signature, API calls, orchestration) lives here so the
route stays thin and the logic is unit-testable with injected fakes.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import jwt

from core.config import settings

logger = logging.getLogger(__name__)


# ── Webhook signature ──────────────────────────────────────────────────────


def verify_webhook_signature(secret: str, body: bytes, signature: str | None) -> bool:
    """Constant-time check of GitHub's ``X-Hub-Signature-256`` header."""
    if not secret or not signature:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── App authentication ─────────────────────────────────────────────────────


def _load_private_key(value: str) -> str:
    """Accept either a PEM string or a path to a .pem file."""
    if "BEGIN" in value and "PRIVATE KEY" in value:
        return value
    p = Path(value)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return value


def build_app_jwt(app_id: str, private_key: str, now: datetime | None = None) -> str:
    """Create a signed app JWT (RS256). Valid for ~9 minutes (<10 min cap)."""
    now = now or datetime.now(tz=UTC)
    payload = {
        # 60s back-dating tolerates minor clock skew (recommended by GitHub).
        "iat": int(now.timestamp()) - 60,
        "exp": int((now + timedelta(minutes=9)).timestamp()),
        "iss": app_id,
    }
    return jwt.encode(payload, _load_private_key(private_key), algorithm="RS256")


class GitHubClient:
    """Minimal async GitHub REST client for the review bot."""

    def __init__(self, token: str, api_base: str | None = None, http: httpx.AsyncClient | None = None):
        self._token = token
        self._api = (api_base or settings.github_api_base).rstrip("/")
        self._http = http or httpx.AsyncClient(timeout=30.0)
        self._owns_http = http is None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @classmethod
    async def for_installation(cls, installation_id: int, http: httpx.AsyncClient | None = None) -> GitHubClient:
        """Mint an installation token from the app credentials and wrap it."""
        app_jwt = build_app_jwt(settings.github_app_id, settings.github_app_private_key)
        client = http or httpx.AsyncClient(timeout=30.0)
        api = settings.github_api_base.rstrip("/")
        resp = await client.post(
            f"{api}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        resp.raise_for_status()
        token = resp.json()["token"]
        return cls(token, api_base=api, http=client)

    async def get_pull_request_files(self, repo: str, number: int) -> list[dict]:
        resp = await self._http.get(
            f"{self._api}/repos/{repo}/pulls/{number}/files",
            headers=self._headers(), params={"per_page": 100},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_review(self, repo: str, number: int, body: str,
                            comments: list[dict], event: str = "COMMENT") -> dict:
        """Post a PR review. ``comments`` use GitHub's inline-comment shape."""
        payload: dict[str, Any] = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments
        resp = await self._http.post(
            f"{self._api}/repos/{repo}/pulls/{number}/reviews",
            headers=self._headers(), json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def create_check_run(self, repo: str, head_sha: str, *, conclusion: str,
                               title: str, summary: str) -> dict:
        resp = await self._http.post(
            f"{self._api}/repos/{repo}/check-runs",
            headers=self._headers(),
            json={
                "name": "AgentForge Review",
                "head_sha": head_sha,
                "status": "completed",
                "conclusion": conclusion,  # success | failure | neutral
                "output": {"title": title, "summary": summary},
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        if self._owns_http:
            await self._http.aclose()


# ── Review of a PR ─────────────────────────────────────────────────────────


async def default_pr_reviewer(filename: str, patch: str) -> list[dict]:
    """Run AgentForge's structured reviewer over a single file's diff.

    Returns a list of ``Finding`` dicts. Reuses the injection guard and the
    validated ``ReviewOutput`` contract so the bot's output is structured.
    """
    from agents.sanitize import wrap_untrusted
    from agents.utils import parse_structured
    from core.providers import get_provider
    from models.agent_outputs import ReviewOutput

    model = settings.github_review_model
    provider = get_provider(model)
    system = (
        "You are AgentForge's code reviewer. Review the provided unified diff and "
        "report concrete bugs, security issues, and missing edge cases. "
        'Output ONLY JSON: {"verdict":"pass|fail|review_needed","summary":"...",'
        '"findings":[{"severity":"critical|high|medium|low|info","title":"...",'
        '"detail":"...","line":0,"suggestion":"..."}]}. Max 5 findings.'
    )
    safe = wrap_untrusted(f"File: {filename}\n{patch}", "diff", 12_000)
    try:
        resp = await provider.chat(model, system, safe, max_tokens=900)
    except Exception as e:  # provider/network failure shouldn't crash the webhook
        logger.warning("PR reviewer failed for %s: %s", filename, e)
        return []
    review = parse_structured(resp.content, ReviewOutput)
    if review is None:
        return []
    out = []
    for f in review.findings:
        d = f.model_dump()
        d["file"] = filename
        out.append(d)
    return out


def _findings_to_comments(filename: str, findings: list[dict]) -> list[dict]:
    """Map findings with a line number to GitHub inline review comments."""
    comments = []
    for f in findings:
        line = f.get("line")
        if not line:
            continue
        body = f"**[{f.get('severity', 'info')}] {f.get('title', 'issue')}**\n\n{f.get('detail', '')}"
        if f.get("suggestion"):
            body += f"\n\n_Suggestion:_ {f['suggestion']}"
        comments.append({"path": filename, "line": int(line), "body": body})
    return comments


_BLOCKING = {"critical", "high"}


async def handle_pull_request_event(
    payload: dict,
    *,
    client_factory=GitHubClient.for_installation,
    reviewer=default_pr_reviewer,
) -> dict:
    """Review an opened/synchronized PR and post results.

    ``client_factory`` and ``reviewer`` are injectable for testing. Returns a
    summary dict describing what was posted.
    """
    action = payload.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        return {"skipped": f"action={action}"}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    number = pr["number"]
    head_sha = pr["head"]["sha"]
    installation_id = payload.get("installation", {}).get("id")
    if installation_id is None:
        return {"skipped": "no installation id"}

    client = await client_factory(installation_id)
    try:
        files = await client.get_pull_request_files(repo, number)
        all_findings: list[dict] = []
        comments: list[dict] = []
        for f in files:
            patch = f.get("patch")
            if not patch or f.get("status") == "removed":
                continue
            findings = await reviewer(f["filename"], patch)
            all_findings.extend(findings)
            comments.extend(_findings_to_comments(f["filename"], findings))

        blocking = sum(1 for f in all_findings if str(f.get("severity", "")).lower() in _BLOCKING)
        if all_findings:
            summary = (
                f"AgentForge reviewed {len(files)} file(s) and found "
                f"{len(all_findings)} issue(s), {blocking} blocking."
            )
        else:
            summary = f"AgentForge reviewed {len(files)} file(s): no issues found. ✅"

        await client.create_review(
            repo, number, body=summary, comments=comments,
            event="REQUEST_CHANGES" if blocking else "COMMENT",
        )
        await client.create_check_run(
            repo, head_sha,
            conclusion="failure" if blocking else "success",
            title="AgentForge Review",
            summary=summary,
        )
        return {
            "repo": repo, "pr": number,
            "files_reviewed": len(files),
            "findings": len(all_findings),
            "blocking": blocking,
        }
    finally:
        await client.close()

"""Thin HTTP client for the AgentForge API with token storage + auto-refresh."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

DEFAULT_API = "http://localhost:8000/api/v1"


def config_path() -> Path:
    """Location of the CLI config (override with AGENTFORGE_CLI_CONFIG for tests)."""
    override = os.environ.get("AGENTFORGE_CLI_CONFIG")
    if override:
        return Path(override)
    return Path.home() / ".agentforge" / "config.json"


def load_config() -> dict:
    p = config_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def save_config(cfg: dict) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(p, 0o600)  # tokens are sensitive
    except OSError:
        pass


class APIError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status}: {detail}")


class AgentForgeClient:
    """Authenticated API client.

    Transparently refreshes the access token once on a 401 using the stored
    refresh token, mirroring the web client's behavior.
    """

    def __init__(self, api_url: str | None = None, config: dict | None = None,
                 http: httpx.Client | None = None):
        self._cfg = config if config is not None else load_config()
        self.api_url = (api_url or self._cfg.get("api_url") or DEFAULT_API).rstrip("/")
        self._http = http or httpx.Client(timeout=120.0)
        self._owns_http = http is None

    # â”€â”€ auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def login(self, email: str, password: str) -> dict:
        data = self._raw("POST", "/auth/login", json={"email": email, "password": password})
        self._cfg.update({
            "api_url": self.api_url,
            "token": data["token"],
            "refresh_token": data["refresh_token"],
            "email": data.get("email", email),
        })
        save_config(self._cfg)
        return data

    def logout(self) -> None:
        refresh = self._cfg.get("refresh_token")
        if refresh:
            try:
                self._authed("POST", "/auth/logout", json={"refresh_token": refresh})
            except APIError:
                pass
        for k in ("token", "refresh_token", "email"):
            self._cfg.pop(k, None)
        save_config(self._cfg)

    def _refresh(self) -> bool:
        refresh = self._cfg.get("refresh_token")
        if not refresh:
            return False
        try:
            data = self._raw("POST", "/auth/refresh", json={"refresh_token": refresh})
        except APIError:
            return False
        self._cfg["token"] = data["token"]
        self._cfg["refresh_token"] = data["refresh_token"]
        save_config(self._cfg)
        return True

    # â”€â”€ requests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _raw(self, method: str, path: str, **kw):
        resp = self._http.request(method, f"{self.api_url}{path}", **kw)
        if resp.status_code >= 400:
            raise APIError(resp.status_code, _detail(resp))
        return resp.json() if resp.content else {}

    def _authed(self, method: str, path: str, _retry: bool = True, **kw):
        token = self._cfg.get("token")
        if not token:
            raise APIError(401, "Not logged in. Run `agentforge login` first.")
        headers = {**kw.pop("headers", {}), "Authorization": f"Bearer {token}"}
        resp = self._http.request(method, f"{self.api_url}{path}", headers=headers, **kw)
        if resp.status_code == 401 and _retry and self._refresh():
            return self._authed(method, path, _retry=False, **kw)
        if resp.status_code >= 400:
            raise APIError(resp.status_code, _detail(resp))
        return resp.json() if resp.content else {}

    # â”€â”€ review â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def submit_review(self, code: str, language: str | None = None) -> str:
        body = {"code": code}
        if language:
            body["language"] = language
        data = self._authed("POST", "/review", json=body)
        return data["review_id"]

    def get_review(self, review_id: str) -> dict:
        return self._authed("GET", f"/review/{review_id}")

    def review_and_wait(self, code: str, language: str | None = None,
                        poll_interval: float = 1.0, timeout: float = 120.0,
                        sleep=time.sleep) -> dict:
        review_id = self.submit_review(code, language)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = self.get_review(review_id)
            if result.get("status") in ("completed", "failed", "error"):
                return result
            sleep(poll_interval)
        raise APIError(408, f"Review {review_id} timed out after {timeout}s")

    # â”€â”€ tasks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def create_task(self, team_id: str, title: str, description: str,
                    project_id: str | None = None) -> dict:
        body = {"team_id": team_id, "title": title, "description": description}
        if project_id:
            body["project_id"] = project_id
        return self._authed("POST", "/tasks", json=body)

    def get_task(self, task_id: str) -> dict:
        return self._authed("GET", f"/tasks/{task_id}")

    def close(self):
        if self._owns_http:
            self._http.close()


def _detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict) and "detail" in body:
            return str(body["detail"])
    except ValueError:
        pass
    return resp.text[:300] or resp.reason_phrase

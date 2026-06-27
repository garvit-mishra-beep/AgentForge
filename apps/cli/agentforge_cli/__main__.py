"""``agentforge`` CLI entry point."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from agentforge_cli import __version__
from agentforge_cli.client import AgentForgeClient, APIError

_SEV_ORDER = {"critical": 0, "high": 1, "major": 1, "medium": 2, "low": 3, "info": 4, "minor": 3}


def _print_issues(result: dict) -> int:
    """Print review issues; return process exit code (non-zero if blocking)."""
    issues = result.get("issues") or []
    status = result.get("status")
    if status not in ("completed",):
        print(f"Review {status}: {result.get('error') or ''}".rstrip())
        return 1

    if not issues:
        print("✓ No issues found.")
        return 0

    issues = sorted(issues, key=lambda i: _SEV_ORDER.get(str(i.get("severity", "")).lower(), 5))
    blocking = 0
    for i in issues:
        sev = str(i.get("severity", "info")).lower()
        marker = "✗" if sev in ("critical", "high", "major") else "•"
        if sev in ("critical", "high", "major"):
            blocking += 1
        line = f" (line {i['line']})" if i.get("line") else ""
        print(f"{marker} [{sev}] {i.get('title', 'issue')}{line}")
        if i.get("description"):
            print(f"    {i['description']}")
        if i.get("suggestion"):
            print(f"    fix: {i['suggestion']}")
    if result.get("summary"):
        print(f"\n{result['summary']}")
    print(f"\n{len(issues)} issue(s), {blocking} blocking.")
    return 1 if blocking else 0


def cmd_login(args, client_factory) -> int:
    email = args.email or input("Email: ")
    password = args.password or getpass.getpass("Password: ")
    client = client_factory(args.api)
    try:
        data = client.login(email, password)
    except APIError as e:
        print(f"Login failed: {e.detail}", file=sys.stderr)
        return 1
    finally:
        client.close()
    print(f"Logged in as {data.get('email', email)}.")
    return 0


def cmd_logout(args, client_factory) -> int:
    client = client_factory(args.api)
    try:
        client.logout()
    finally:
        client.close()
    print("Logged out.")
    return 0


def cmd_review(args, client_factory) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    code = path.read_text(encoding="utf-8", errors="replace")
    if not code.strip():
        print("File is empty.", file=sys.stderr)
        return 2
    client = client_factory(args.api)
    try:
        result = client.review_and_wait(code, language=args.language, timeout=args.timeout)
    except APIError as e:
        print(f"Review failed: {e.detail}", file=sys.stderr)
        return 1
    finally:
        client.close()
    return _print_issues(result)


def cmd_task(args, client_factory) -> int:
    client = client_factory(args.api)
    try:
        task = client.create_task(args.team, args.title, args.description, args.project)
    except APIError as e:
        print(f"Task creation failed: {e.detail}", file=sys.stderr)
        return 1
    finally:
        client.close()
    print(f"Task {task['id']} created (status: {task['status']}).")
    return 0


def cmd_status(args, client_factory) -> int:
    client = client_factory(args.api)
    try:
        task = client.get_task(args.task_id)
    except APIError as e:
        print(f"Lookup failed: {e.detail}", file=sys.stderr)
        return 1
    finally:
        client.close()
    print(f"{task['id']}  {task['status']}  {task.get('title', '')}")
    if task.get("error_message"):
        print(f"  error: {task['error_message']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentforge", description="AgentForge CLI")
    p.add_argument("--version", action="version", version=f"agentforge {__version__}")
    p.add_argument("--api", default=None, help="API base URL (default: stored or http://localhost:8000/api/v1)")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("login", help="Authenticate and store a token")
    sp.add_argument("--email")
    sp.add_argument("--password")
    sp.set_defaults(func=cmd_login)

    sp = sub.add_parser("logout", help="Revoke the stored token")
    sp.set_defaults(func=cmd_logout)

    sp = sub.add_parser("review", help="Review a source file")
    sp.add_argument("file")
    sp.add_argument("--language", default=None)
    sp.add_argument("--timeout", type=float, default=120.0)
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("task", help="Create a task")
    sp.add_argument("--team", required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--description", required=True)
    sp.add_argument("--project", default=None)
    sp.set_defaults(func=cmd_task)

    sp = sub.add_parser("status", help="Show a task's status")
    sp.add_argument("task_id")
    sp.set_defaults(func=cmd_status)

    return p


def main(argv=None, client_factory=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    factory = client_factory or (lambda api: AgentForgeClient(api_url=api))
    return args.func(args, factory)


if __name__ == "__main__":
    sys.exit(main())

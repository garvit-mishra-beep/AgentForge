"""Security and observability tests."""

import pytest

import json
import logging

from core.encryption import EncryptionService
from core.logging_config import JSONFormatter, setup_logging
from core.observability import generate_correlation_id, get_request_metrics
from core.redis import rate_limit_check, rate_limit_reset, failed_login_attempt, is_login_locked, reset_login_attempts, brute_force_reset
from app.routes.projects import _sanitize_filename, _ALLOWED_EXTENSIONS


@pytest.mark.asyncio
async def test_encryption_roundtrip():
    service = EncryptionService()
    plaintext = "sk-test-key-1234567890abcdef"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    assert decrypted == plaintext


@pytest.mark.asyncio
async def test_encryption_different_ivs():
    service = EncryptionService()
    plaintext = "sk-test-key-1234567890abcdef"
    encrypted1 = service.encrypt(plaintext)
    encrypted2 = service.encrypt(plaintext)
    assert encrypted1 != encrypted2


@pytest.mark.asyncio
async def test_encryption_mask_key():
    service = EncryptionService()
    key = "sk-ant-1234567890abcdef"
    masked = service.mask_key(key)
    assert "cdef" in masked
    assert "1234567890" not in masked
    assert "****" in masked or "••••" in masked


@pytest.mark.asyncio
async def test_encryption_short_key():
    service = EncryptionService()
    key = "abc"
    masked = service.mask_key(key)
    assert masked == "****"


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    await rate_limit_reset()
    ip = "192.168.1.1"
    for _ in range(5):
        allowed = await rate_limit_check(ip, limit=10, window=3600)
        assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks_at_limit():
    await rate_limit_reset()
    ip = "192.168.1.2"
    for _ in range(10):
        await rate_limit_check(ip, limit=10, window=3600)

    allowed = await rate_limit_check(ip, limit=10, window=3600)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_reset():
    await rate_limit_reset()
    ip = "192.168.1.3"
    for _ in range(10):
        await rate_limit_check(ip, limit=10, window=3600)

    assert await rate_limit_check(ip, limit=10, window=3600) is False
    await rate_limit_reset()
    assert await rate_limit_check(ip, limit=10, window=3600) is True


@pytest.mark.asyncio
async def test_rate_limiter_different_ips_independent():
    await rate_limit_reset()
    for _ in range(10):
        await rate_limit_check("ip-a", limit=10, window=3600)

    assert await rate_limit_check("ip-a", limit=10, window=3600) is False
    assert await rate_limit_check("ip-b", limit=10, window=3600) is True


@pytest.mark.asyncio
async def test_rate_limiter_window_expiry():
    await rate_limit_reset()
    ip = "192.168.1.4"
    for _ in range(10):
        await rate_limit_check(ip, limit=10, window=1)

    assert await rate_limit_check(ip, limit=10, window=1) is False

    import time
    time.sleep(1.1)

    allowed = await rate_limit_check(ip, limit=10, window=1)
    assert allowed is True


# ── Brute Force Protection ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_brute_force_allows_within_limit():
    await brute_force_reset()
    for _ in range(4):
        count = await failed_login_attempt("test-user-1", lockout_seconds=60)
        assert count <= 4
    locked = await is_login_locked("test-user-1", max_attempts=5, lockout_seconds=60)
    assert locked is False


@pytest.mark.asyncio
async def test_brute_force_locks_after_limit():
    await brute_force_reset()
    for _ in range(5):
        await failed_login_attempt("test-user-2", lockout_seconds=60)
    locked = await is_login_locked("test-user-2", max_attempts=5, lockout_seconds=60)
    assert locked is True


@pytest.mark.asyncio
async def test_brute_force_reset_clears():
    await brute_force_reset()
    for _ in range(5):
        await failed_login_attempt("test-user-3", lockout_seconds=60)
    assert await is_login_locked("test-user-3", max_attempts=5, lockout_seconds=60) is True
    await reset_login_attempts("test-user-3")
    assert await is_login_locked("test-user-3", max_attempts=5, lockout_seconds=60) is False


@pytest.mark.asyncio
async def test_brute_force_different_users_independent():
    await brute_force_reset()
    for _ in range(5):
        await failed_login_attempt("locked-user", lockout_seconds=60)
    await failed_login_attempt("free-user", lockout_seconds=60)
    assert await is_login_locked("locked-user", max_attempts=5, lockout_seconds=60) is True
    assert await is_login_locked("free-user", max_attempts=5, lockout_seconds=60) is False


# ── Rate Limiter Key Prefix ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limiter_different_prefixes_independent():
    await rate_limit_reset()
    ip = "10.0.0.1"
    for _ in range(10):
        await rate_limit_check(ip, limit=10, window=3600, key_prefix="prefix_a:")
    assert await rate_limit_check(ip, limit=10, window=3600, key_prefix="prefix_a:") is False
    assert await rate_limit_check(ip, limit=10, window=3600, key_prefix="prefix_b:") is True


# ── Filename Sanitization ─────────────────────────────────────────────


def test_sanitize_filename_removes_path_separators():
    assert _sanitize_filename("../../etc/passwd") == "passwd"
    assert _sanitize_filename("foo\\..\\bar") == "bar"
    assert _sanitize_filename("foo/bar/baz.py") == "baz.py"


def test_sanitize_filename_removes_dangerous_chars():
    safe = _sanitize_filename("hello<world>.py")
    assert "<" not in safe
    assert ">" not in safe


def test_sanitize_filename_allows_valid():
    assert _sanitize_filename("main.py") == "main.py"
    assert _sanitize_filename("my file.js") == "my file.js"
    assert _sanitize_filename("README.md") == "README.md"


def test_sanitize_filename_empty_becomes_random():
    result = _sanitize_filename(".")
    assert result.startswith("upload_")
    result = _sanitize_filename("..")
    assert result.startswith("upload_")
    result = _sanitize_filename("")
    assert result.startswith("upload_")


def test_allowed_extensions_contains_common_types():
    for ext in [".py", ".js", ".ts", ".json", ".md", ".html", ".css", ".yaml", ".yml", ".sql"]:
        assert ext in _ALLOWED_EXTENSIONS


# ── Observability ────────────────────────────────────────────────────


def test_generate_correlation_id_returns_uuid():
    cid = generate_correlation_id()
    assert len(cid) == 36
    assert cid.count("-") == 4


def test_correlation_id_is_unique():
    ids = {generate_correlation_id() for _ in range(100)}
    assert len(ids) == 100


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    resp = await client.get("/api/v1/metrics")
    assert resp.status_code == 200
    assert "agentforge_requests_total" in resp.text
    assert "agentforge_request_duration_ms" in resp.text
    assert "agentforge_active_background_tasks" in resp.text


@pytest.mark.asyncio
async def test_correlation_id_header_on_response(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert "x-correlation-id" in resp.headers
    assert len(resp.headers["x-correlation-id"]) == 36


@pytest.mark.asyncio
async def test_correlation_id_passthrough(client):
    cid = "test-correlation-id-123"
    resp = await client.get("/api/v1/health", headers={"x-correlation-id": cid})
    assert resp.headers.get("x-correlation-id") == cid


@pytest.mark.asyncio
async def test_metrics_tracks_requests(client):
    await client.get("/api/v1/health")
    metrics = get_request_metrics()
    recent = [m for m in metrics if m.path == "/api/v1/health"]
    assert len(recent) >= 1


# ── Security Headers ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_security_headers_present(client):
    resp = await client.get("/api/v1/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"
    assert resp.headers.get("strict-transport-security") is not None
    assert resp.headers.get("cache-control") == "no-store"


# ── JSON Logging ──────────────────────────────────────────────────


def test_json_formatter_produces_valid_json():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["name"] == "test.logger"
    assert parsed["message"] == "hello world"
    assert "timestamp" in parsed


def test_json_formatter_includes_correlation_id():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="test", args=(), exc_info=None,
    )
    record.correlation_id = "cid-123"
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["correlation_id"] == "cid-123"


def test_json_formatter_includes_exception():
    import sys
    formatter = JSONFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname=__file__, lineno=1,
            msg="error occurred", args=(), exc_info=exc_info,
        )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "ERROR"
    assert "exception" in parsed
    assert "test error" in parsed["exception"] or "ValueError" in parsed["exception"]


def test_setup_logging_json_format():
    setup_logging("DEBUG", "json")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    # Reset back to text for test output
    setup_logging("INFO", "text")


def test_setup_logging_text_format():
    setup_logging("WARNING", "text")
    root = logging.getLogger()
    assert root.level == logging.WARNING
    setup_logging("INFO", "text")

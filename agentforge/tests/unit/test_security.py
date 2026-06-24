from __future__ import annotations

import sys
import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, PropertyMock

sys.path.insert(0, "C:\\Users\\garvi\\AgentOS\\agentforge")

import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from apps.api.core.config import settings, validate_settings, Settings
from apps.api.core.security import (
    create_access_token, create_refresh_token, verify_token,
    hash_password, verify_password, JWT_ISSUER,
)
from apps.api.services.rag import TextChunker, RAGPipeline
from apps.api.services.vector_store import EmbeddingService
from packages.workflows.src import safe_eval, SafeEvalError

# ==============================================================================
# SECTION 1: JWT & TOKEN SECURITY TESTS
# ==============================================================================

class TestJWT:
    def test_valid_token_creation(self):
        token = create_access_token(subject="testuser", tenant_id="tenant-1")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["tenant_id"] == "tenant-1"
        assert payload["iss"] == JWT_ISSUER
        assert payload["aud"] == settings.JWT_AUDIENCE
        assert "jti" in payload
        assert payload["type"] == "access"

    def test_token_has_unique_jti(self):
        t1 = create_access_token(subject="user1", tenant_id="t1")
        t2 = create_access_token(subject="user1", tenant_id="t1")
        p1 = verify_token(t1)
        p2 = verify_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_refresh_token_type(self):
        token = create_refresh_token(subject="testuser", tenant_id="t1")
        payload = verify_token(token)
        assert payload["type"] == "refresh"

    def test_expired_token_is_rejected(self):
        import jwt as pyjwt
        from datetime import timedelta, timezone
        expired_payload = {
            "sub": "testuser",
            "tenant_id": "t1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "iss": JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "jti": "test-jti",
            "type": "access",
        }
        token = pyjwt.encode(expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        payload = verify_token(token)
        assert payload is None

    def test_invalid_audience_rejected(self):
        token = jwt.encode(
            {"sub": "user", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "aud": "wrong-audience", "iss": JWT_ISSUER, "jti": "x", "type": "access"},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        payload = verify_token(token)
        assert payload is None

    def test_invalid_issuer_rejected(self):
        token = jwt.encode(
            {"sub": "user", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "aud": settings.JWT_AUDIENCE, "iss": "attacker", "jti": "x", "type": "access"},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        payload = verify_token(token)
        assert payload is None

    def test_malformed_token_rejected(self):
        payload = verify_token("not-a-valid-jwt-token")
        assert payload is None

    def test_tampered_token_rejected(self):
        token = create_access_token(subject="user", tenant_id="t1")
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".invalidsignature"
        payload = verify_token(tampered)
        assert payload is None

    def test_token_with_wrong_secret_rejected(self):
        token = jwt.encode(
            {"sub": "user", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "aud": settings.JWT_AUDIENCE, "iss": JWT_ISSUER, "jti": "x", "type": "access"},
            "wrong-secret",
            algorithm=settings.JWT_ALGORITHM,
        )
        payload = verify_token(token)
        assert payload is None


# ==============================================================================
# SECTION 2: JWT SECRET VALIDATION TESTS
# ==============================================================================

class TestJWTSecretValidation:
    def test_empty_secret_rejected(self):
        with pytest.raises(SystemExit):
            validate_settings(Settings(JWT_SECRET=""))

    def test_default_secret_rejected(self):
        with pytest.raises(SystemExit):
            validate_settings(Settings(JWT_SECRET="change-this-in-production"))

    def test_valid_secret_accepted(self):
        s = Settings(JWT_SECRET="sufficiently-long-secret-key-for-hmac-sha256")
        validate_settings(s)

    def test_whitespace_only_secret_rejected(self):
        with pytest.raises(SystemExit):
            validate_settings(Settings(JWT_SECRET="   "))


# ==============================================================================
# SECTION 3: PASSWORD SECURITY TESTS
# ==============================================================================

class TestPasswordSecurity:
    def test_hash_verification_roundtrip(self):
        password = "MySecureP@ssw0rd!2024"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_rejected(self):
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_empty_password_rejected(self):
        hashed = hash_password("real-password")
        assert not verify_password("", hashed)

    def test_hash_is_different_each_time(self):
        pwd = "test-password"
        h1 = hash_password(pwd)
        h2 = hash_password(pwd)
        assert h1 != h2  # bcrypt uses different salts


# ==============================================================================
# SECTION 4: TENANT ISOLATION TESTS
# ==============================================================================

class TestAgentServiceTenantIsolation:
    @pytest.mark.asyncio
    async def test_get_filters_by_tenant(self):
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()
        tenant_b = uuid.uuid4()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        from apps.api.services import AgentService
        service = AgentService(mock_db)

        result = await service.get(agent_id, tenant_id=tenant_b)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_filters_by_tenant(self):
        mock_db = AsyncMock()
        from apps.api.services import AgentService
        from apps.api.schemas import AgentUpdate

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        service = AgentService(mock_db)
        result = await service.update(uuid.uuid4(), AgentUpdate(name="test"), tenant_id=uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_filters_by_tenant(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        from apps.api.services import AgentService
        service = AgentService(mock_db)
        result = await service.delete(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is False


class TestWorkflowServiceTenantIsolation:
    @pytest.mark.asyncio
    async def test_get_filters_by_tenant(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        from apps.api.services import WorkflowService
        service = WorkflowService(mock_db)

        wf_id = uuid.uuid4()
        result = await service.get(wf_id, tenant_id=uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_filters_by_tenant(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        from apps.api.services import WorkflowService
        service = WorkflowService(mock_db)
        result = await service.delete(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is False


class TestExecutionServiceTenantIsolation:
    @pytest.mark.asyncio
    async def test_get_filters_by_tenant(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        from apps.api.services import ExecutionService
        service = ExecutionService(mock_db)

        result = await service.get(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is None


# ==============================================================================
# SECTION 5: SAFE EVAL TESTS
# ==============================================================================

class TestSafeEval:
    def test_simple_comparison(self):
        result = safe_eval("state['x'] == 5", {"state": {"x": 5}})
        assert result is True

    def test_not_equal(self):
        assert safe_eval("state.x != 5", {"state": type("obj", (), {"x": 10})()}) is True

    def test_greater_than(self):
        assert safe_eval("state['x'] > 5", {"state": {"x": 10}}) is True

    def test_less_than_or_equal(self):
        assert safe_eval("state['x'] <= 5", {"state": {"x": 5}}) is True

    def test_and_operator(self):
        assert safe_eval("state.a and state.b", {"state": {"a": True, "b": True}}) is True
        assert safe_eval("state.a and state.b", {"state": {"a": True, "b": False}}) is False

    def test_or_operator(self):
        assert safe_eval("state.a or state.b", {"state": {"a": False, "b": True}}) is True

    def test_not_operator(self):
        assert safe_eval("not state.x", {"state": {"x": False}}) is True
        assert safe_eval("not state.x", {"state": {"x": True}}) is False

    def test_list_literal(self):
        result = safe_eval("[1, 2, 3]", {"state": {}})
        assert result == [1, 2, 3]

    def test_dict_literal(self):
        result = safe_eval('{"key": "value"}', {"state": {}})
        assert result == {"key": "value"}

    def test_subscript_on_context(self):
        assert safe_eval("state['items'][0]", {"state": {"items": [1, 2, 3]}}) == 1

    def test_arithmetic(self):
        assert safe_eval("state.x + state.y", {"state": {"x": 10, "y": 5}}) == 15
        assert safe_eval("state.x - state.y", {"state": {"x": 10, "y": 5}}) == 5
        assert safe_eval("state.x * state.y", {"state": {"x": 10, "y": 5}}) == 50
        assert safe_eval("state.x / state.y", {"state": {"x": 10, "y": 5}}) == 2.0

    def test_negation(self):
        assert safe_eval("-state.x", {"state": {"x": 5}}) == -5

    # --- Forbidden operations ---

    def test_imports_rejected(self):
        with pytest.raises(SafeEvalError):
            safe_eval("__import__('os')", {"state": {}})

    def test_function_calls_rejected(self):
        with pytest.raises(SafeEvalError):
            safe_eval("state['x'].__class__", {"state": {"x": "hello"}})

    def test_attribute_access_on_unknown_rejected(self):
        with pytest.raises(SafeEvalError):
            safe_eval("__builtins__['eval']", {"state": {}})

    def test_lambda_rejected(self):
        with pytest.raises(SafeEvalError):
            safe_eval("lambda x: x", {"state": {}})

    def test_undefined_name_rejected(self):
        with pytest.raises(SafeEvalError):
            safe_eval("undefined_var", {"state": {}})


# ==============================================================================
# SECTION 6: FILE UPLOAD SECURITY TESTS
# ==============================================================================

class TestUploadSecurity:
    def test_allowed_mime_types(self):
        assert "application/pdf" in settings.ALLOWED_UPLOAD_MIME_TYPES
        assert "text/plain" in settings.ALLOWED_UPLOAD_MIME_TYPES
        assert "text/markdown" in settings.ALLOWED_UPLOAD_MIME_TYPES

    def test_rejected_mime_types_not_present(self):
        assert "application/x-executable" not in settings.ALLOWED_UPLOAD_MIME_TYPES
        assert "application/zip" not in settings.ALLOWED_UPLOAD_MIME_TYPES
        assert "application/x-msdownload" not in settings.ALLOWED_UPLOAD_MIME_TYPES
        assert "application/x-sh" not in settings.ALLOWED_UPLOAD_MIME_TYPES

    def test_max_upload_size_defined(self):
        assert settings.MAX_UPLOAD_SIZE > 0
        assert settings.MAX_UPLOAD_SIZE == 10 * 1024 * 1024  # 10 MB


# ==============================================================================
# SECTION 7: TEXT CHUNKER TESTS
# ==============================================================================

class TestTextChunker:
    def test_short_text_single_chunk(self):
        chunker = TextChunker(chunk_size=1000, chunk_overlap=0)
        chunks = chunker.chunk_text("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_long_text_multiple_chunks(self):
        chunker = TextChunker(chunk_size=10, chunk_overlap=2)
        text = "A" * 25
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2

    def test_empty_text(self):
        chunker = TextChunker()
        chunks = chunker.chunk_text("")
        assert len(chunks) == 1 and chunks[0] == ""

    def test_overlap_produces_overlapping_chunks(self):
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "X" * 50
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2


# ==============================================================================
# SECTION 8: METRICS FILTERING TESTS
# ==============================================================================

class TestMetricsDaysFiltering:
    @pytest.mark.asyncio
    async def test_get_metrics_applies_days_filter(self):
        mock_db = AsyncMock()

        class FakeResult:
            one = lambda self: [10, 5000, 0.05, 1500.0]

        async def fake_execute(_stmt):
            return FakeResult()

        mock_db.execute = fake_execute

        from apps.api.services import ExecutionService
        service = ExecutionService(mock_db)

        result = await service.get_metrics(uuid.uuid4(), days=7)
        assert result["total_executions"] == 10
        assert result["total_tokens"] == 5000


# ==============================================================================
# SECTION 9: EMBEDDING SERVICE TESTS
# ==============================================================================

class TestEmbeddingService:
    def test_mock_embed_returns_correct_dimension(self):
        svc = EmbeddingService(api_key=None)
        import asyncio
        result = asyncio.run(svc.embed(["test text"]))
        assert len(result) == 1
        assert len(result[0]) == 1536

    def test_mock_embed_multiple_texts(self):
        svc = EmbeddingService(api_key=None)
        import asyncio
        result = asyncio.run(svc.embed(["text a", "text b"]))
        assert len(result) == 2


# ==============================================================================
# SECTION 10: RAG RETURN TYPE TESTS
# ==============================================================================

class TestRAGReturnType:
    @pytest.mark.asyncio
    async def test_ingest_returns_int(self):
        rag_pipeline = RAGPipeline(collection_prefix="test")
        with patch.object(rag_pipeline.chunker, "chunk_text", return_value=["chunk1", "chunk2"]):
            with patch("apps.api.services.rag.vector_store") as mock_vs:
                mock_vs.ensure_collection = AsyncMock(return_value=True)
                mock_vs.upsert_points = AsyncMock(return_value=2)
                count = await rag_pipeline.ingest_document(
                    tenant_id="test-tenant",
                    document_id="doc-1",
                    text="test document text",
                )
                assert isinstance(count, int)
                assert count == 2


# ==============================================================================
# SECTION 11: HEALTH CHECK TESTS
# ==============================================================================

class TestHealth:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "qdrant" in data["checks"]


# ==============================================================================
# SECTION 12: ROOT ENDPOINT
# ==============================================================================

class TestRoot:
    @pytest.mark.asyncio
    async def test_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data


# ==============================================================================
# SECTION 13: MODEL TESTS
# ==============================================================================

class TestModels:
    def test_agent_has_tenant_id(self):
        from apps.api.models import Agent
        cols = [c.name for c in Agent.__table__.columns]
        assert "tenant_id" in cols
        assert "llm_config" in cols

    def test_execution_has_foreign_keys(self):
        from apps.api.models import Execution
        cols = [c.name for c in Execution.__table__.columns]
        assert "agent_id" in cols
        assert "workflow_id" in cols
        assert "tenant_id" in cols

    def test_user_model_exists(self):
        from apps.api.models import User
        cols = [c.name for c in User.__table__.columns]
        assert "username" in cols
        assert "password_hash" in cols
        assert "tenant_id" in cols
        assert "is_active" in cols


# ==============================================================================
# SECTION 14: VALIDATION SCHEMA TESTS
# ==============================================================================

class TestSchemas:
    def test_agent_create_validates_slug(self):
        from apps.api.schemas import AgentCreate
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            AgentCreate(name="test", slug="INVALID SLUG with spaces")

    def test_agent_create_validates_name_length(self):
        from apps.api.schemas import AgentCreate
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            AgentCreate(name="", slug="test-slug")

    def test_agent_create_valid_slug(self):
        from apps.api.schemas import AgentCreate
        agent = AgentCreate(name="Test", slug="valid-slug-123")
        assert agent.name == "Test"
        assert agent.slug == "valid-slug-123"


# ==============================================================================
# SECTION 15: EXCEPTION TESTS
# ==============================================================================

class TestExceptions:
    def test_not_found_exception(self):
        from apps.api.core.exceptions import NotFoundException
        exc = NotFoundException("Agent not found")
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"

    def test_auth_exception(self):
        from apps.api.core.exceptions import AuthenticationException
        exc = AuthenticationException("Invalid token")
        assert exc.status_code == 401
        assert exc.error_code == "UNAUTHORIZED"


# ==============================================================================
# SECTION 16: API KEY AUTH TESTS
# ==============================================================================

class TestAPIKeyAuth:
    def test_api_key_model_has_expiry(self):
        from apps.api.models import APIKey
        cols = [c.name for c in APIKey.__table__.columns]
        assert "expires_at" in cols
        assert "key_hash" in cols
        assert "permissions" in cols


# ==============================================================================
# SECTION 17: ROUTE REGISTRATION TESTS
# ==============================================================================

class TestRouteRegistration:
    def test_all_routes_registered(self, client):
        auth_routes = [r.path for r in client._transport.app.routes if hasattr(r, "path") and "auth" in r.path]
        assert len(auth_routes) >= 4
        agent_routes = [r.path for r in client._transport.app.routes if hasattr(r, "path") and "agents" in r.path]
        assert len(agent_routes) >= 6
        rag_routes = [r.path for r in client._transport.app.routes if hasattr(r, "path") and "rag" in r.path]
        assert len(rag_routes) >= 5

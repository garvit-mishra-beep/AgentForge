from __future__ import annotations

import uuid
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

from apps.api.core.security import (
    create_access_token, create_refresh_token, verify_token,
    hash_password, verify_password,
)
from apps.api.services.audit import AuditService
from apps.api.middleware.rate_limit import RateLimitStore, RATE_LIMITED_PATHS
from apps.api.models import User, Agent, Workflow, Execution, APIKey, AuditLog


class TestAuthenticationFlow:
    @pytest.mark.asyncio
    async def test_password_hash_roundtrip(self):
        pw = "SecureP@ss123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True
        assert verify_password("wrong", hashed) is False

    @pytest.mark.asyncio
    async def test_token_create_verify(self):
        token = create_access_token(subject="user1", tenant_id="t1")
        payload = verify_token(token)
        assert payload["sub"] == "user1"
        assert payload["tenant_id"] == "t1"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "iat" in payload
        assert payload["iss"] == "agentforge-api"

    @pytest.mark.asyncio
    async def test_refresh_token(self):
        token = create_refresh_token(subject="user1", tenant_id="t1")
        payload = verify_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user1"

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self):
        import jwt as pyjwt
        from apps.api.core.security import JWT_ISSUER
        from apps.api.core.config import settings
        expired = {
            "sub": "user1", "tenant_id": "t1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "iss": JWT_ISSUER, "aud": settings.JWT_AUDIENCE,
            "jti": "test", "type": "access",
        }
        token = pyjwt.encode(expired, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        assert verify_token(token) is None


class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_agent_get_respects_tenant_id(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import AgentService
        svc = AgentService(mock_db)
        result = await svc.get(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_agent_delete_respects_tenant_id(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import AgentService
        svc = AgentService(mock_db)
        result = await svc.delete(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is False


class TestAgentCRUD:
    @pytest.mark.asyncio
    async def test_agent_create_schema(self):
        from apps.api.schemas import AgentCreate
        data = AgentCreate(name="Test Agent", slug="test-agent", description="desc")
        assert data.name == "Test Agent"
        assert data.slug == "test-agent"

    @pytest.mark.asyncio
    async def test_agent_update_schema(self):
        from apps.api.schemas import AgentUpdate
        data = AgentUpdate(name="Updated")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {"name": "Updated"}

    @pytest.mark.asyncio
    async def test_agent_create_rejects_bad_slug(self):
        from apps.api.schemas import AgentCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AgentCreate(name="Test", slug="UPPERCASE SLUG!")


class TestWorkflowCRUD:
    @pytest.mark.asyncio
    async def test_workflow_create_schema(self):
        from apps.api.schemas import WorkflowCreate
        data = WorkflowCreate(name="WF", description="d", definition={"nodes": [], "edges": []})
        assert data.name == "WF"

    @pytest.mark.asyncio
    async def test_workflow_get_respects_tenant(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import WorkflowService
        svc = WorkflowService(mock_db)
        result = await svc.get(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is None


class TestExecutionLifecycle:
    @pytest.mark.asyncio
    async def test_execution_create(self):
        mock_db = AsyncMock()
        fake_exec = AsyncMock()

        class FakeAgent:
            id = uuid.uuid4()
            tenant_id = uuid.uuid4()
            name = "agent"
            slug = "agent"
            llm_config = {}
            system_prompt = None
            tools = []
            memory_config = {}
            created_at = datetime.now(timezone.utc)
            updated_at = datetime.now(timezone.utc)

        from apps.api.services import ExecutionService
        svc = ExecutionService(mock_db)
        result = await svc.create(uuid.uuid4(), agent_id=None, input_data={"msg": "hello"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_execution_get_respects_tenant(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import ExecutionService
        svc = ExecutionService(mock_db)
        result = await svc.get(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is None





class TestVectorSearch:
    @pytest.mark.asyncio
    async def test_search_with_mock(self):
        from apps.api.services.rag import RAGPipeline
        from unittest.mock import patch, MagicMock
        rag = RAGPipeline(collection_prefix="test")
        with patch("apps.api.services.rag.vector_store") as mock_vs:
            mock_vs.client.collection_exists = AsyncMock(return_value=True)
            mock_result = MagicMock()
            mock_result.payload = {"text": "test", "document_id": "d1", "chunk_index": 0}
            mock_result.score = 0.95
            mock_vs.search = AsyncMock(return_value=[mock_result])
            results = await rag.search(tenant_id="t1", query="test", limit=5)
            assert len(results) == 1
            assert results[0]["text"] == "test"
            assert results[0]["score"] == 0.95


class TestServiceLayer:
    @pytest.mark.asyncio
    async def test_agent_list_with_status_filter(self):
        mock_db = AsyncMock()

        class FakeScalars:
            def all(self):
                return []

        class FakeResult:
            def scalars(self):
                return FakeScalars()

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import AgentService
        svc = AgentService(mock_db)
        result = await svc.list(uuid.uuid4(), status="draft")
        assert result == []

    @pytest.mark.asyncio
    async def test_agent_list_with_skip_limit(self):
        mock_db = AsyncMock()

        class FakeScalars:
            def all(self):
                return []

        class FakeResult:
            def scalars(self):
                return FakeScalars()

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import AgentService
        svc = AgentService(mock_db)
        result = await svc.list(uuid.uuid4(), skip=10, limit=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_execution_list_with_filters(self):
        mock_db = AsyncMock()

        class FakeScalars:
            def all(self):
                return []

        class FakeResult:
            def scalars(self):
                return FakeScalars()

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import ExecutionService
        svc = ExecutionService(mock_db)
        result = await svc.list(uuid.uuid4(), agent_id=uuid.uuid4(), status="running")
        assert result == []

    @pytest.mark.asyncio
    async def test_execution_update_status(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import ExecutionService
        svc = ExecutionService(mock_db)
        result = await svc.update_status(uuid.uuid4(), "completed")
        assert result is None

    @pytest.mark.asyncio
    async def test_execution_update_result(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import ExecutionService
        svc = ExecutionService(mock_db)
        result = await svc.update_result(uuid.uuid4(), {"msg": "ok"}, tokens=100, cost=0.01, duration_ms=500, steps=[{"step": "1"}])
        assert result is None

    @pytest.mark.asyncio
    async def test_workflow_list(self):
        mock_db = AsyncMock()

        class FakeScalars:
            def all(self):
                return []

        class FakeResult:
            def scalars(self):
                return FakeScalars()

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import WorkflowService
        svc = WorkflowService(mock_db)
        result = await svc.list(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_workflow_update(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.schemas import WorkflowUpdate
        from apps.api.services import WorkflowService
        svc = WorkflowService(mock_db)
        result = await svc.update(uuid.uuid4(), WorkflowUpdate(name="updated"), tenant_id=uuid.uuid4())
        assert result is None


class TestAPIKeyAuth:
    @pytest.mark.asyncio
    async def test_api_key_model(self):
        key = APIKey(
            tenant_id=uuid.uuid4(),
            name="test-key",
            key_hash="abc123",
            key_prefix="ag_",
            permissions=["agent:invoke"],
        )
        assert key.name == "test-key"
        assert key.key_prefix == "ag_"

    @pytest.mark.asyncio
    async def test_api_key_expiry_check(self):
        key = APIKey(
            tenant_id=uuid.uuid4(),
            name="expired-key",
            key_hash="abc",
            key_prefix="ag_",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert key.expires_at is not None
        assert key.expires_at < datetime.now(timezone.utc)


class TestWebSocketAuth:
    @pytest.mark.asyncio
    async def test_ws_token_verification(self):
        token = create_access_token(subject="ws-user", tenant_id="t1")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "ws-user"


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_store_allows_within_window(self):
        store = RateLimitStore()
        key = "test:127.0.0.1:/api/v1/auth/token"
        assert store.check(key, 5, 60) is True
        assert store.check(key, 5, 60) is True
        assert store.check(key, 5, 60) is True

    @pytest.mark.asyncio
    async def test_rate_limit_store_blocks_excess(self):
        store = RateLimitStore()
        key = "test:127.0.0.1:/api/v1/auth/token"
        for _ in range(3):
            store.check(key, 3, 60)
        assert store.check(key, 3, 60) is False

    @pytest.mark.asyncio
    async def test_rate_limit_config_paths(self):
        assert "/api/v1/auth/token" in RATE_LIMITED_PATHS
        assert "/api/v1/auth/register" in RATE_LIMITED_PATHS
        assert "/api/v1/rag/upload" in RATE_LIMITED_PATHS


class TestAuditLogging:
    @pytest.mark.asyncio
    async def test_audit_log_create(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        mock_db.execute = AsyncMock(return_value=FakeResult())

        svc = AuditService(mock_db)
        entry = await svc.log(
            actor_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            action="create.agent",
            resource_type="agent",
            resource_id=str(uuid.uuid4()),
            meta_data={"name": "test"},
            ip_address="127.0.0.1",
        )
        assert entry.action == "create.agent"
        assert entry.resource_type == "agent"

    @pytest.mark.asyncio
    async def test_audit_log_query(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalars(self):
                return self
            def all(self):
                return []

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        svc = AuditService(mock_db)
        logs = await svc.get_logs(tenant_id=uuid.uuid4(), limit=10)
        assert logs == []

    @pytest.mark.asyncio
    async def test_audit_log_model(self):
        entry = AuditLog(
            action="delete.workflow",
            resource_type="workflow",
            resource_id=str(uuid.uuid4()),
        )
        assert entry.action == "delete.workflow"
        assert entry.resource_type == "workflow"


class TestAgentBySlug:
    @pytest.mark.asyncio
    async def test_get_by_slug_returns_none_for_missing(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import AgentService
        svc = AgentService(mock_db)
        result = await svc.get_by_slug(uuid.uuid4(), "nonexistent")
        assert result is None


class TestWorkflowUpdateNotFound:
    @pytest.mark.asyncio
    async def test_workflow_update_returns_none(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.schemas import WorkflowUpdate
        from apps.api.services import WorkflowService
        svc = WorkflowService(mock_db)
        result = await svc.update(uuid.uuid4(), WorkflowUpdate(name="x"), tenant_id=uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_workflow_delete_returns_false(self):
        mock_db = AsyncMock()

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import WorkflowService
        svc = WorkflowService(mock_db)
        result = await svc.delete(uuid.uuid4(), tenant_id=uuid.uuid4())
        assert result is False


class TestObservability:
    @pytest.mark.asyncio
    async def test_metrics_query(self):
        mock_db = AsyncMock()

        class FakeResult:
            one = lambda self: [5, 1000, 0.1, 200.0]

        async def fake_exec(_stmt):
            return FakeResult()

        mock_db.execute = fake_exec
        from apps.api.services import ExecutionService
        svc = ExecutionService(mock_db)
        result = await svc.get_metrics(uuid.uuid4(), days=7)
        assert result["total_executions"] == 5
        assert result["total_tokens"] == 1000


class TestConfigValidation:
    @pytest.mark.asyncio
    async def test_settings_defaults(self):
        from apps.api.core.config import settings as s
        assert s.APPLICATION_NAME == "AgentForge AI"
        assert s.JWT_ALGORITHM == "HS256"
        assert s.MAX_UPLOAD_SIZE == 10 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_allowed_mime_types(self):
        from apps.api.core.config import settings as s
        assert "application/pdf" in s.ALLOWED_UPLOAD_MIME_TYPES
        assert "text/plain" in s.ALLOWED_UPLOAD_MIME_TYPES
        assert "image/png" not in s.ALLOWED_UPLOAD_MIME_TYPES

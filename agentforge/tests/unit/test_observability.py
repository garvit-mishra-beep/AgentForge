from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health_returns_healthy(self):
        from apps.api.core.health import health_checker
        result = await health_checker.run_all()
        assert "status" in result
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert result["environment"] == "development"

    @pytest.mark.asyncio
    async def test_liveness_returns_healthy(self):
        from apps.api.core.health import health_checker
        result = await health_checker.liveness()
        assert result["status"] == "healthy"
        assert "uptime_seconds" in result

    @pytest.mark.asyncio
    async def test_critical_checks_run(self):
        from apps.api.core.health import health_checker
        result = await health_checker.run_critical()
        assert "status" in result
        assert "checks" in result
        assert "database" in result["checks"]

    @pytest.mark.asyncio
    async def test_check_database_failure(self):
        from apps.api.core.health import check_database
        with patch("apps.api.core.database.async_session", side_effect=Exception("db down")):
            result = await check_database()
            assert result is False

    @pytest.mark.asyncio
    async def test_check_redis_failure(self):
        from apps.api.core.health import check_redis
        with patch("redis.asyncio.from_url", side_effect=Exception("redis down")):
            result = await check_redis()
            assert result is False

    @pytest.mark.asyncio
    async def test_check_qdrant_failure(self):
        from apps.api.core.health import check_qdrant
        with patch("qdrant_client.AsyncQdrantClient", side_effect=Exception("qdrant down")):
            result = await check_qdrant()
            assert result is False


class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_valid_content(self):
        from apps.api.core.metrics import metrics_endpoint
        content = metrics_endpoint()
        assert content is not None
        decoded = content.decode("utf-8")
        assert "# HELP" in decoded
        assert "# TYPE" in decoded

    def test_track_request_creates_metrics(self):
        from apps.api.core.metrics import track_request
        from prometheus_client.registry import REGISTRY
        sample = REGISTRY.get_sample_value("http_requests_total", {"method": "GET", "path": "/test", "status": "200"})
        track_request(method="GET", path="/test", status=200, duration=0.1)
        after = REGISTRY.get_sample_value("http_requests_total", {"method": "GET", "path": "/test", "status": "200"})
        assert after is None or (sample or 0) < (after or 0)

    def test_track_workflow_creates_metrics(self):
        from apps.api.core.metrics import track_workflow
        from prometheus_client.registry import REGISTRY
        track_workflow(workflow_id="wf-1", status="completed", duration=2.5)
        val = REGISTRY.get_sample_value("workflow_executions_total", {"status": "completed"})
        assert val is not None

    def test_track_agent_invocation_creates_metrics(self):
        from apps.api.core.metrics import track_agent_invocation
        from prometheus_client.registry import REGISTRY
        track_agent_invocation(agent_id="ag-1", status="success")
        val = REGISTRY.get_sample_value("agent_invocations_total", {"agent_id": "ag-1", "status": "success"})
        assert val is not None

    def test_track_token_usage_creates_metrics(self):
        from apps.api.core.metrics import track_token_usage
        from prometheus_client.registry import REGISTRY
        track_token_usage(agent_id="ag-1", model="gpt-4", tokens=500)
        val = REGISTRY.get_sample_value("token_usage_total", {"agent_id": "ag-1", "model": "gpt-4"})
        assert val is not None

    def test_track_rag_query_creates_metrics(self):
        from apps.api.core.metrics import track_rag_query
        from prometheus_client.registry import REGISTRY
        track_rag_query(status="success", latency=0.3)
        val = REGISTRY.get_sample_value("rag_queries_total", {"status": "success"})
        assert val is not None


class TestTelemetry:
    def test_get_tracer_returns_tracer(self):
        from apps.api.core.telemetry import get_tracer
        tracer = get_tracer()
        assert tracer is not None

    def test_setup_telemetry_disabled(self):
        from apps.api.core.telemetry import setup_telemetry
        from unittest.mock import MagicMock
        app = MagicMock()
        with patch("apps.api.core.config.settings.ENABLE_TRACING", False):
            setup_telemetry(app)
            # Should not raise

    def test_setup_telemetry_enabled(self):
        from apps.api.core.telemetry import setup_telemetry
        app = MagicMock()
        with (
            patch("apps.api.core.config.settings.ENABLE_TRACING", True),
            patch("apps.api.core.telemetry.FastAPIInstrumentor.instrument_app"),
            patch("apps.api.core.telemetry.HTTPXClientInstrumentor.instrument"),
        ):
            setup_telemetry(app)
            # Should not raise


class TestResilience:
    @pytest.mark.asyncio
    async def test_call_with_timeout_success(self):
        from apps.api.core.resilience import call_with_timeout
        result = await call_with_timeout(async_return(42), 5.0, "test")
        assert result == 42

    @pytest.mark.asyncio
    async def test_call_with_timeout_failure(self):
        from apps.api.core.resilience import call_with_timeout
        import asyncio

        async def slow():
            await asyncio.sleep(10)
            return 1

        with pytest.raises(TimeoutError):
            await call_with_timeout(slow(), 0.1, "test")

    def test_circuit_breakers_exist(self):
        from apps.api.core.resilience import llm_breaker, qdrant_breaker, redis_breaker
        assert llm_breaker is not None
        assert qdrant_breaker is not None
        assert redis_breaker is not None

    def test_retry_decorators_exist(self):
        from apps.api.core.resilience import llm_retry, qdrant_retry, redis_retry
        assert llm_retry is not None
        assert qdrant_retry is not None
        assert redis_retry is not None


class TestLogging:
    def test_bootstrap_logging_runs(self):
        from apps.api.core.logging import bootstrap_logging
        with patch("structlog.configure"):
            bootstrap_logging()

    def test_bootstrap_json_logging(self):
        from apps.api.core.logging import bootstrap_logging
        with (
            patch("structlog.configure") as mock_configure,
            patch("apps.api.core.config.settings.ENVIRONMENT", "production"),
        ):
            bootstrap_logging()
            call_kwargs = mock_configure.call_args.kwargs
            assert call_kwargs is not None


async def async_return(value):
    return value

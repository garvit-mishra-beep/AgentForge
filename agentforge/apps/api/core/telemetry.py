from __future__ import annotations

import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from apps.api.core.config import settings

logger = logging.getLogger(__name__)

_tracer: trace.Tracer | None = None


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


def setup_telemetry(app, db_engine=None) -> None:
    if not settings.ENABLE_TRACING:
        logger.info("OpenTelemetry tracing is disabled")
        return
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=f"{settings.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    if db_engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=db_engine)
    logger.info("OpenTelemetry tracing enabled, exporting to %s", settings.OTEL_EXPORTER_OTLP_ENDPOINT)

"""Metrics (Prometheus) and tracing (OpenTelemetry) wiring.

- Metrics: a ``/metrics`` endpoint (Prometheus format) plus default HTTP latency
  histograms, enabled by ``METRICS_ENABLED`` (on by default).
- Tracing: FastAPI is auto-instrumented and an explicit ``engine.process_action``
  span is recorded in the websocket layer. Spans print to the console in dev, or
  export to an OTLP collector when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set. Tracing
  is enabled by ``OTEL_ENABLED`` (off by default — no collector needed locally).

See docs/references/observability.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

if TYPE_CHECKING:
    from fastapi import FastAPI

    from app.settings.config import Settings


def setup_observability(app: FastAPI, settings: Settings) -> None:
    """Wire metrics and (optionally) tracing into the FastAPI app."""
    if settings.metrics_enabled:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app, include_in_schema=False)

    if settings.otel_enabled:
        _setup_tracing(app, settings)


def _setup_tracing(app: FastAPI, settings: Settings) -> None:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    provider = TracerProvider(resource=Resource.create({"service.name": settings.service_name}))

    if settings.otel_exporter_otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        # Batch export to the OTLP collector in production.
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)))
    else:
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        # Print spans immediately to the console for local debugging.
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str = "app.game.engine") -> trace.Tracer:
    """Return an OTel tracer. A no-op until tracing is enabled, so it is always safe to call."""
    return trace.get_tracer(name)

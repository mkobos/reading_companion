import logging
import os

from fastapi import FastAPI
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

logger = logging.getLogger(__name__)

_SERVICE_NAME = "reading-companion-backend"


def _cloud_trace_enabled(env: dict) -> bool:
    if env.get("ENABLE_CLOUD_TRACE", "false").lower() not in ("true", "1"):
        return False
    return bool(env.get("GOOGLE_CLOUD_PROJECT"))


def setup_tracing() -> tuple[TracerProvider, bool]:
    """Build a TracerProvider for this process.

    No span processor is attached to a network exporter unless
    OTEL_CONSOLE_EXPORT or ENABLE_CLOUD_TRACE is set, so hermetic tests and
    local dev need no GCP credentials or network access. Cloud exporter
    construction failures are caught and logged rather than raised — a
    Cloud Trace outage or missing credentials must never affect request
    handling (fail-open).
    """
    resource = Resource.create(
        {
            "service.name": _SERVICE_NAME,
            "service.version": os.environ.get("COMMIT_SHA", "dev"),
        }
    )
    provider = TracerProvider(resource=resource)

    if os.environ.get("OTEL_CONSOLE_EXPORT", "false").lower() in ("true", "1"):
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    cloud_enabled = False
    if _cloud_trace_enabled(os.environ):
        try:
            provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
            cloud_enabled = True
        except Exception:
            logger.warning(
                "Cloud Trace exporter setup failed; continuing without cloud "
                "export.",
                exc_info=True,
            )

    return provider, cloud_enabled


def setup_logging() -> None:
    """Configure the root logger.

    LOG_FORMAT=json emits structured JSON to stdout via google-cloud-logging's
    StructuredLogHandler, which auto-correlates log entries with the active
    trace/span context. This makes no network calls and needs no GCP
    credentials — Cloud Run's logging agent scrapes stdout. Default is plain
    text, matching the un-configured behavior every other module here already
    relies on.
    """
    root_logger = logging.getLogger()
    if getattr(root_logger, "_telemetry_configured", False):
        return

    if os.environ.get("LOG_FORMAT", "plain").lower() == "json":
        from google.cloud.logging_v2.handlers import StructuredLogHandler

        handler = StructuredLogHandler()
    else:
        handler = logging.StreamHandler()

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    root_logger._telemetry_configured = True  # type: ignore[attr-defined]


def instrument_app(app: FastAPI, tracer_provider: TracerProvider) -> None:
    """Instrument inbound HTTP and outbound httpx calls with the given provider.

    No request/response body-capture hooks are configured — captured span
    attributes are limited to method, route, and status code. Never enable
    body capture here: document text, notes, and discussion content are
    untrusted/PII-class user content (see agent-contract.yaml's
    untrusted-content inventory) and must never end up in trace data.
    """
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    instrumentor = HTTPXClientInstrumentor()
    if not instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.instrument(tracer_provider=tracer_provider)

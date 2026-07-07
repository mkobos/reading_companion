from fastapi.testclient import TestClient
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.main import create_app


def _traced_client(settings, store, blob_store, discussion_agent_client, llm_client):
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    app = create_app(
        settings=settings,
        store=store,
        blob_store=blob_store,
        discussion_agent_client=discussion_agent_client,
        llm_client=llm_client,
        tracer_provider=provider,
    )
    return TestClient(app), exporter


def test_http_request_produces_a_server_span(
    settings, store, blob_store, discussion_agent_client, llm_client
):
    client, exporter = _traced_client(
        settings, store, blob_store, discussion_agent_client, llm_client
    )

    response = client.post("/api/workspaces")

    assert response.status_code == 201
    spans = exporter.get_finished_spans()
    server_spans = [s for s in spans if s.kind.name == "SERVER"]
    assert len(server_spans) >= 1
    attrs = server_spans[0].attributes
    assert attrs.get("http.status_code") == 201


def test_spans_never_contain_request_or_response_body_text(
    settings, store, blob_store, discussion_agent_client, llm_client
):
    secret_note_text = "SECRET_NOTE_ABOUT_THE_VEIL_OF_IGNORANCE"
    client, exporter = _traced_client(
        settings, store, blob_store, discussion_agent_client, llm_client
    )
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]
    client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes.txt", b"Hello world. Second sentence.", "text/plain")},
    )

    client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={
            "anchor": {
                "first_block_id": "000000",
                "first_block_offset": 0,
                "last_block_id": "000000",
                "last_block_offset": len("Hello world."),
                "text": "Hello world.",
            },
            "text": secret_note_text,
        },
    )

    for span in exporter.get_finished_spans():
        for value in span.attributes.values():
            assert secret_note_text not in str(value)

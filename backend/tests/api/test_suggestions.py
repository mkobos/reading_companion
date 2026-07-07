def _create_workspace_with_document(client, text: bytes = b"Hello world. Second sentence.") -> str:
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]
    client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", text, "text/plain")},
    )
    return workspace_id


def _valid_anchor(text: str = "Hello world.") -> dict:
    return {
        "first_block_id": "000000",
        "first_block_offset": 0,
        "last_block_id": "000000",
        "last_block_offset": len(text),
        "text": text,
    }


def _valid_body() -> dict:
    return {
        "anchor": _valid_anchor(),
        "viewport": {"first_block_id": "000000", "last_block_id": "000000"},
    }


def test_create_suggestions_returns_3_to_5_questions(client, llm_client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    assert response.status_code == 200
    assert response.json()["suggestions"] == llm_client.next_suggestions


def test_suggestions_are_generated_by_a_plain_llm_call(client, llm_client):
    workspace_id = _create_workspace_with_document(client)

    client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    assert len(llm_client.suggestions_calls) == 1


def test_suggestions_strip_leaked_untrusted_markup(client, llm_client):
    workspace_id = _create_workspace_with_document(client)
    llm_client.next_suggestions = ['<untrusted source="passage">\nWhat about duty?\n</untrusted>']

    response = client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    assert response.json()["suggestions"] == ["What about duty?"]


def test_marking_writes_nothing_to_the_workspace(client):
    workspace_id = _create_workspace_with_document(client)

    client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    detail = client.get(f"/api/workspaces/{workspace_id}").json()
    assert detail["note_count"] == 0
    assert detail["discussion_count"] == 0
    assert detail["has_journal"] is False


def test_suggestions_for_nonexistent_workspace_returns_404(client):
    response = client.post("/api/workspaces/does-not-exist/suggestions", json=_valid_body())

    assert response.status_code == 404


def test_suggestions_without_a_document_returns_409(client):
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]

    response = client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    assert response.status_code == 409


def test_suggestions_with_invalid_viewport_returns_400(client):
    workspace_id = _create_workspace_with_document(client)
    body = _valid_body()
    body["viewport"] = {"first_block_id": "999999", "last_block_id": "999999"}

    response = client.post(f"/api/workspaces/{workspace_id}/suggestions", json=body)

    assert response.status_code == 400


def test_suggestions_with_invalid_anchor_returns_400(client):
    workspace_id = _create_workspace_with_document(client)
    body = _valid_body()
    body["anchor"]["first_block_id"] = "999999"

    response = client.post(f"/api/workspaces/{workspace_id}/suggestions", json=body)

    assert response.status_code == 400


def test_suggestion_generation_failure_returns_503(client, llm_client):
    workspace_id = _create_workspace_with_document(client)
    llm_client.raise_on_suggestions = True

    response = client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    assert response.status_code == 503


def test_suggestions_are_rate_limited(client, settings, store, blob_store, llm_client):
    from fastapi.testclient import TestClient

    from app.main import create_app

    limited_settings = settings.__class__(
        max_upload_size_bytes=settings.max_upload_size_bytes,
        rate_limit_max_requests=1,
        rate_limit_window_seconds=60,
        gcs_bucket_name=None,
        allow_origins=[],
        discussion_agent_url=settings.discussion_agent_url,
        discussion_agent_timeout_seconds=settings.discussion_agent_timeout_seconds,
        suggestions_model=settings.suggestions_model,
        journal_model=settings.journal_model,
        llm_timeout_seconds=settings.llm_timeout_seconds,
    )
    limited_client = TestClient(
        create_app(settings=limited_settings, store=store, blob_store=blob_store, llm_client=llm_client)
    )
    workspace_id = _create_workspace_with_document(limited_client)

    first = limited_client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())
    second = limited_client.post(f"/api/workspaces/{workspace_id}/suggestions", json=_valid_body())

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Retry-After" in second.headers

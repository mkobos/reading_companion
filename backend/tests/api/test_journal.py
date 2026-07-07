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


def _add_note(client, workspace_id: str, text: str = "A note about duty.") -> None:
    client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": text},
    )


def test_get_journal_returns_404_before_any_generation(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.get(f"/api/workspaces/{workspace_id}/journal")

    assert response.status_code == 404


def test_get_journal_for_nonexistent_workspace_returns_404(client):
    response = client.get("/api/workspaces/does-not-exist/journal")

    assert response.status_code == 404


def test_generate_journal_with_notes_returns_200_and_persists(client, llm_client):
    workspace_id = _create_workspace_with_document(client)
    _add_note(client, workspace_id)

    response = client.post(f"/api/workspaces/{workspace_id}/journal")

    assert response.status_code == 200
    assert response.json()["text"] == llm_client.next_journal
    assert client.get(f"/api/workspaces/{workspace_id}/journal").json()["text"] == llm_client.next_journal


def test_generate_journal_strips_leaked_untrusted_markup(client, llm_client):
    workspace_id = _create_workspace_with_document(client)
    _add_note(client, workspace_id)
    llm_client.next_journal = '<untrusted source="note">\nSynthesis.\n</untrusted>'

    response = client.post(f"/api/workspaces/{workspace_id}/journal")

    assert response.json()["text"] == "Synthesis."


def test_generate_journal_for_nonexistent_workspace_returns_404(client):
    response = client.post("/api/workspaces/does-not-exist/journal")

    assert response.status_code == 404


def test_generate_journal_with_nothing_to_synthesize_returns_409_and_makes_no_llm_call(
    client, llm_client
):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(f"/api/workspaces/{workspace_id}/journal")

    assert response.status_code == 409
    assert llm_client.journal_calls == []


def test_generation_failure_leaves_prior_journal_intact(client, llm_client):
    workspace_id = _create_workspace_with_document(client)
    _add_note(client, workspace_id)
    client.post(f"/api/workspaces/{workspace_id}/journal")
    original_text = client.get(f"/api/workspaces/{workspace_id}/journal").json()["text"]

    llm_client.raise_on_journal = True
    response = client.post(f"/api/workspaces/{workspace_id}/journal")

    assert response.status_code == 503
    assert client.get(f"/api/workspaces/{workspace_id}/journal").json()["text"] == original_text


def test_regeneration_replaces_the_previous_journal(client, llm_client):
    workspace_id = _create_workspace_with_document(client)
    _add_note(client, workspace_id)
    client.post(f"/api/workspaces/{workspace_id}/journal")

    llm_client.next_journal = "# Journal\n\nUpdated synthesis."
    response = client.post(f"/api/workspaces/{workspace_id}/journal")

    assert response.status_code == 200
    assert response.json()["text"] == "# Journal\n\nUpdated synthesis."
    assert (
        client.get(f"/api/workspaces/{workspace_id}/journal").json()["text"]
        == "# Journal\n\nUpdated synthesis."
    )


def test_workspace_detail_has_journal_reflects_state(client):
    workspace_id = _create_workspace_with_document(client)
    _add_note(client, workspace_id)

    assert client.get(f"/api/workspaces/{workspace_id}").json()["has_journal"] is False

    client.post(f"/api/workspaces/{workspace_id}/journal")

    assert client.get(f"/api/workspaces/{workspace_id}").json()["has_journal"] is True


def test_journal_generation_is_rate_limited_but_get_is_unaffected(client, settings, store, blob_store, llm_client):
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
    _add_note(limited_client, workspace_id)

    first = limited_client.post(f"/api/workspaces/{workspace_id}/journal")
    second = limited_client.post(f"/api/workspaces/{workspace_id}/journal")

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Retry-After" in second.headers

    # GET is unaffected by the write-side limiter (separate limiter instance).
    get_response = limited_client.get(f"/api/workspaces/{workspace_id}/journal")
    assert get_response.status_code == 200

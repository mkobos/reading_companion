def test_create_workspace_returns_high_entropy_id(client):
    response = client.post("/api/workspaces")

    assert response.status_code == 201
    body = response.json()
    assert len(body["workspace_id"]) >= 22
    assert "created_at" in body


def test_get_workspace_returns_detail(client):
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]

    response = client.get(f"/api/workspaces/{workspace_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["workspace_id"] == workspace_id
    assert body["has_document"] is False
    assert body["note_count"] == 0
    assert body["discussion_count"] == 0
    assert body["has_journal"] is False


def test_get_nonexistent_workspace_returns_404(client):
    response = client.get("/api/workspaces/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"message": "Not found"}


def test_get_malformed_workspace_id_returns_identical_404(client):
    nonexistent = client.get("/api/workspaces/does-not-exist")
    malformed = client.get("/api/workspaces/!!!not-a-valid-token!!!")

    assert malformed.status_code == 404
    assert malformed.json() == nonexistent.json()


def test_delete_workspace_removes_it(client):
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]

    delete_response = client.delete(f"/api/workspaces/{workspace_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/workspaces/{workspace_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_workspace_returns_404(client):
    response = client.delete("/api/workspaces/does-not-exist")

    assert response.status_code == 404


def test_getting_or_deleting_bad_id_does_not_create_a_workspace(client, store):
    client.get("/api/workspaces/some-bad-id")
    client.delete("/api/workspaces/some-bad-id")

    assert client.get("/api/workspaces/some-bad-id").status_code == 404


def test_workspaces_are_isolated_from_each_other(client):
    workspace_a = client.post("/api/workspaces").json()["workspace_id"]
    workspace_b = client.post("/api/workspaces").json()["workspace_id"]

    client.post(
        f"/api/workspaces/{workspace_a}/document",
        files={"file": ("a.txt", b"Workspace A content", "text/plain")},
    )

    response_b = client.get(f"/api/workspaces/{workspace_b}/document")
    assert response_b.status_code == 404

    response_a = client.get(f"/api/workspaces/{workspace_a}/document")
    assert response_a.status_code == 200
    assert "Workspace A content" in response_a.json()["blocks"][0]["text"]


def test_workspace_creation_is_rate_limited(client, settings, store, blob_store):
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
    limited_app = create_app(settings=limited_settings, store=store, blob_store=blob_store)
    from fastapi.testclient import TestClient

    limited_client = TestClient(limited_app)

    first = limited_client.post("/api/workspaces")
    second = limited_client.post("/api/workspaces")

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Retry-After" in second.headers

def _create_workspace(client) -> str:
    return client.post("/api/workspaces").json()["workspace_id"]


def test_upload_plain_text_document(client):
    workspace_id = _create_workspace(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes.txt", b"Hello world.", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "text"
    assert body["filename"] == "notes.txt"
    assert body["blocks"] == [
        {"block_id": "000000", "type": "paragraph", "text": "Hello world.", "level": None}
    ]
    assert "raw_blob_ref" not in body


def test_upload_markdown_document(client):
    workspace_id = _create_workspace(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.md", b"# Title\nBody text.", "text/markdown")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "markdown"
    assert body["blocks"][0] == {
        "block_id": "000000",
        "type": "heading",
        "text": "Title",
        "level": 1,
    }


def test_get_document_after_upload(client):
    workspace_id = _create_workspace(client)
    client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes.txt", b"Hello world.", "text/plain")},
    )

    response = client.get(f"/api/workspaces/{workspace_id}/document")

    assert response.status_code == 200
    assert response.json()["blocks"][0]["text"] == "Hello world."


def test_get_document_before_upload_returns_404(client):
    workspace_id = _create_workspace(client)

    response = client.get(f"/api/workspaces/{workspace_id}/document")

    assert response.status_code == 404


def test_upload_to_nonexistent_workspace_returns_404(client):
    response = client.post(
        "/api/workspaces/does-not-exist/document",
        files={"file": ("notes.txt", b"Hello.", "text/plain")},
    )

    assert response.status_code == 404


def test_document_is_immutable(client):
    workspace_id = _create_workspace(client)
    client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes.txt", b"First upload.", "text/plain")},
    )

    second = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes2.txt", b"Second upload.", "text/plain")},
    )

    assert second.status_code == 409
    unchanged = client.get(f"/api/workspaces/{workspace_id}/document")
    assert unchanged.json()["blocks"][0]["text"] == "First upload."


def test_rejecting_unsupported_file_type(client):
    workspace_id = _create_workspace(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("malware.exe", b"binary junk", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "text" in response.json()["message"] or "Markdown" in response.json()["message"]
    assert client.get(f"/api/workspaces/{workspace_id}/document").status_code == 404


def test_rejecting_oversized_file(client, settings):
    workspace_id = _create_workspace(client)
    oversized = b"x" * (settings.max_upload_size_bytes + 1)

    response = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("big.txt", oversized, "text/plain")},
    )

    assert response.status_code == 400
    assert str(settings.max_upload_size_bytes) in response.json()["message"]
    assert client.get(f"/api/workspaces/{workspace_id}/document").status_code == 404


def test_rejecting_invalid_utf8(client):
    workspace_id = _create_workspace(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("bad.txt", b"\xff\xfe not utf8", "text/plain")},
    )

    assert response.status_code == 400
    assert client.get(f"/api/workspaces/{workspace_id}/document").status_code == 404


def test_malicious_markdown_is_neutralized_end_to_end(client):
    workspace_id = _create_workspace(client)
    markdown = (
        b"<script>alert('inject')</script>\n\n"
        b"[Click me](javascript:alert(1))\n\n"
        b"Plain text.\n"
    )

    response = client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.md", markdown, "text/markdown")},
    )

    assert response.status_code == 201
    texts = [b["text"] for b in response.json()["blocks"]]
    assert texts == ["Click me", "Plain text."]


def test_document_upload_is_rate_limited(client):
    from app.rate_limit import SlidingWindowRateLimiter

    # Use the generous default `client` app (so workspace creation itself
    # isn't limited) and tighten only the document-upload IP limiter.
    client.app.state.document_upload_ip_limiter = SlidingWindowRateLimiter(
        max_requests=1, window_seconds=60
    )

    workspace_a = _create_workspace(client)
    workspace_b = _create_workspace(client)

    first = client.post(
        f"/api/workspaces/{workspace_a}/document",
        files={"file": ("a.txt", b"content", "text/plain")},
    )
    second = client.post(
        f"/api/workspaces/{workspace_b}/document",
        files={"file": ("b.txt", b"content", "text/plain")},
    )

    assert first.status_code == 201
    # Second upload is a different workspace but the same client IP, so the
    # per-IP limiter (not the per-workspace one) should trip.
    assert second.status_code == 429
    assert "Retry-After" in second.headers

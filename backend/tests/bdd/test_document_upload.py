import os

from pytest_bdd import given, parsers, scenario, then, when

from tests.bdd.conftest import FEATURES_DIR

FEATURE = os.path.join(FEATURES_DIR, "document-upload.feature")


@given(parsers.parse('an empty workspace "{label}" with no document'), target_fixture="workspace_id")
def _empty_workspace(bdd_client, bdd_state, label):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_state[label] = workspace_id
    return workspace_id


@scenario(FEATURE, "Rejecting an unsupported file type")
def test_rejecting_unsupported_file_type():
    pass


@when(
    "the user uploads a file with a disallowed extension or content type",
    target_fixture="response",
)
def _upload_disallowed_file(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("malware.exe", b"binary junk", "application/octet-stream")},
    )


@then("the upload is rejected with a message naming the supported formats")
def _rejected_naming_formats(response):
    assert response.status_code == 400
    message = response.json()["message"]
    assert "text" in message.lower() or "markdown" in message.lower()


@then("nothing is stored in the blob store or document store")
def _nothing_stored(bdd_client, workspace_id):
    assert bdd_client.get(f"/api/workspaces/{workspace_id}/document").status_code == 404


@scenario(FEATURE, "Rejecting an oversized file")
def test_rejecting_oversized_file():
    pass


@when("the user uploads a file exceeding the configured size limit", target_fixture="response")
def _upload_oversized_file(bdd_client, workspace_id):
    oversized = b"x" * 2000
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("big.txt", oversized, "text/plain")},
    )


@then("the upload is rejected before the body is fully processed")
def _rejected_oversized(response):
    assert response.status_code == 400


@then("the message states the size limit")
def _message_states_size_limit(response, bdd_client):
    limit = bdd_client.app.state.settings.max_upload_size_bytes
    assert str(limit) in response.json()["message"]


@scenario(FEATURE, "Rejecting invalid text encoding")
def test_rejecting_invalid_text_encoding():
    pass


@when(
    "the user uploads a file that is not valid UTF-8 text", target_fixture="response"
)
def _upload_invalid_encoding(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("bad.txt", b"\xff\xfe not utf8", "text/plain")},
    )


@then("the upload is rejected with an encoding error message")
def _rejected_encoding(response):
    assert response.status_code == 400
    assert "utf-8" in response.json()["message"].lower()


@then("nothing is stored")
def _nothing_stored_generic(bdd_client, workspace_id):
    assert bdd_client.get(f"/api/workspaces/{workspace_id}/document").status_code == 404


@scenario(FEATURE, "Malicious Markdown content is neutralized")
def test_malicious_markdown_content_is_neutralized():
    pass


@when(
    "the user uploads a Markdown file with content:",
    target_fixture="response",
)
def _upload_markdown_content(bdd_client, workspace_id, docstring):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.md", docstring.encode("utf-8"), "text/markdown")},
    )


@then("parsing succeeds with raw HTML dropped and links flattened to their text:")
def _parsing_succeeds_neutralized(response):
    assert response.status_code == 201
    texts = [b["text"] for b in response.json()["blocks"]]
    assert texts == ["Click me", "Plain text."]


@then("the rendered reading view does not execute any script or active link")
def _no_script_or_active_link(response):
    body = response.text
    assert "<script>" not in body
    assert "javascript:" not in body


@scenario(FEATURE, "Document is immutable once uploaded")
def test_document_is_immutable_once_uploaded():
    pass


@given('workspace "W" already has a document', target_fixture="workspace_id")
def _workspace_with_document(bdd_client, bdd_state):
    workspace_id = bdd_state.get("W") or bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_state["W"] = workspace_id
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("first.txt", b"Original content.", "text/plain")},
    )
    return workspace_id


@when("the user attempts to upload another document to workspace \"W\"", target_fixture="response")
def _upload_second_document(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("second.txt", b"Replacement content.", "text/plain")},
    )


@then("the upload is rejected")
def _upload_rejected(response):
    assert response.status_code == 409


@then("the user is directed to create a new workspace for a new document")
def _directed_to_new_workspace(response):
    assert "workspace" in response.json()["message"].lower()

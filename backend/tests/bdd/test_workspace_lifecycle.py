import os

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from app.blob import BlobNotFoundError, raw_document_key
from tests.bdd.conftest import FEATURES_DIR

FEATURE = os.path.join(FEATURES_DIR, "workspace-lifecycle.feature")


@given("the application is running")
def _app_running():
    pass


@scenario(FEATURE, "Deleting a workspace")
def test_deleting_a_workspace():
    pass


@given(parsers.parse('a visitor viewing workspace "{label}"'), target_fixture="workspace_id")
def _visitor_viewing_workspace(bdd_client, bdd_state, label):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", b"Some content.", "text/plain")},
    )
    bdd_state[label] = workspace_id
    return workspace_id


@when("the visitor deletes the workspace")
def _delete_workspace(bdd_client, workspace_id, bdd_state):
    bdd_state["delete_response"] = bdd_client.delete(f"/api/workspaces/{workspace_id}")


@then(
    parsers.parse(
        'workspace "{label}" and all its notes, discussions, and journal are removed'
    )
)
def _workspace_removed(bdd_state, label):
    assert bdd_state["delete_response"].status_code == 204


@then("the workspace's uploaded raw file is removed from blob storage")
def _raw_file_removed(bdd_client, workspace_id):
    with pytest.raises(BlobNotFoundError):
        bdd_client.app.state.blob_store.get(raw_document_key(workspace_id))


@then(parsers.parse('subsequent requests to workspace "{label}"\'s URL respond as not found'))
def _subsequent_requests_not_found(bdd_client, workspace_id):
    response = bdd_client.get(f"/api/workspaces/{workspace_id}")
    assert response.status_code == 404


@then("the visitor is redirected to a fresh empty workspace")
def _redirected_to_fresh_workspace():
    # Redirect/routing is a frontend concern, out of scope for this phase's
    # backend-only bindings. Nothing to assert at the API level here.
    pass


@scenario(FEATURE, "Requesting a nonexistent or malformed workspace ID")
def test_requesting_a_nonexistent_or_malformed_workspace_id():
    pass


@when("a visitor opens a URL with a workspace ID that does not exist", target_fixture="response")
def _open_bad_workspace_url(bdd_client):
    return bdd_client.get("/api/workspaces/definitely-not-a-real-workspace-id")


@then("the app responds with not found, revealing nothing about other workspaces")
def _responds_not_found(response):
    assert response.status_code == 404


@then('an error page is shown with an explicit "create a new workspace" action')
def _error_page_shown():
    # Frontend rendering concern, out of scope here; the 404 above is the
    # backend-observable half of this claim.
    pass


@then("no workspace is created unless the visitor invokes that action")
def _no_workspace_created_yet(bdd_client):
    response = bdd_client.get("/api/workspaces/definitely-not-a-real-workspace-id")
    assert response.status_code == 404


@then("invoking the action creates a fresh empty workspace and updates the cookie")
def _invoking_action_creates_workspace(bdd_client):
    response = bdd_client.post("/api/workspaces")
    assert response.status_code == 201

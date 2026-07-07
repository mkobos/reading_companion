"""Backend-observable scenario from spec/features/reading-view.feature.

Only "Viewport range accompanies discussion requests" is bound here — the
others (rendering, scroll tracking, margin indicators) are entirely
frontend/client-side concerns with no backend surface, consistent with this
repo's convention of only binding API-observable scenarios (see
tests/bdd/test_notes.py's docstring precedent).
"""

import os

from pytest_bdd import given, scenario, then, when

from tests.bdd.conftest import FEATURES_DIR

FEATURE = os.path.join(FEATURES_DIR, "reading-view.feature")

# 48 short blocks so blocks "000040" through "000047" exist, kept small
# because the shared bdd settings fixture caps uploads at 1024 bytes
# (multipart framing overhead counts against that cap too).
_DOCUMENT_TEXT = "\n\n".join(f"S{i}." for i in range(48))


@given('workspace "W" contains a parsed document of many blocks', target_fixture="workspace_id")
def _workspace_with_many_blocks(bdd_client, bdd_state):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", _DOCUMENT_TEXT.encode(), "text/plain")},
    )
    bdd_state["W"] = workspace_id
    return workspace_id


@scenario(FEATURE, "Viewport range accompanies discussion requests")
def test_viewport_range_accompanies_discussion_requests():
    pass


@given('the user\'s active viewport is blocks "000040" through "000047"')
def _active_viewport():
    # The concrete IDs are supplied directly in the request built below;
    # nothing to set up ahead of time (ephemeral client-side tracking state).
    pass


@when(
    "the user marks a passage and sends a discussion message", target_fixture="discussion_response"
)
def _mark_passage_and_send_message(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={
            "message": "What's happening here?",
            "viewport": {"first_block_id": "000040", "last_block_id": "000047"},
            "anchor": {
                "first_block_id": "000040",
                "first_block_offset": 0,
                "last_block_id": "000040",
                "last_block_offset": len("S40."),
                "text": "S40.",
            },
        },
    )


@then("the discussion request is sent with only the active viewport block range IDs")
def _request_sends_only_block_range_ids(discussion_response):
    # api.openapi.yaml's Viewport schema is exactly {first_block_id,
    # last_block_id} — the client never has an opportunity to send full
    # block text, only IDs; this is a request-shape guarantee, not a
    # runtime check to make on the response.
    assert discussion_response.status_code == 201


@then("the backend resolves the viewport text from those block IDs")
def _backend_resolves_viewport_text(bdd_discussion_agent_client):
    context = bdd_discussion_agent_client.run_turn_calls[0]["context"]
    viewport_text = context["viewport_text"]
    assert '<block id="000040">S40.</block>' in viewport_text
    assert '<block id="000047">S47.</block>' in viewport_text

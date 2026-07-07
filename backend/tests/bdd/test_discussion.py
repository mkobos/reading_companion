"""Backend-observable, untagged scenarios from spec/features/discussion.feature.

@eval-tagged scenarios (underspecified questions, tool-invocation content,
continuing-a-discussion response quality) are discussion-agent's eval-harness
responsibility per spec/features/README.md — not bound here. Named
@scenario bindings, not scenarios(path), so those stay unbound rather than
erroring (matches this repo's existing convention, e.g. tests/bdd/test_notes.py).

Uses bdd_discussion_agent_client (a scripted fake, see tests/conftest.py's
FakeDiscussionAgentClient) — never a live model call from the backend suite;
discussion-agent's own eval harness is what actually judges response quality.
"""

import os

from pytest_bdd import given, parsers, scenario, then, when

from tests.bdd.conftest import FEATURES_DIR

FEATURE = os.path.join(FEATURES_DIR, "discussion.feature")

_DOCUMENT_TEXT = "The categorical imperative is Kant's central moral principle."


def _anchor_for(text: str, offset: int = 0) -> dict:
    return {
        "first_block_id": "000000",
        "first_block_offset": offset,
        "last_block_id": "000000",
        "last_block_offset": offset + len(text),
        "text": text,
    }


_VIEWPORT = {"first_block_id": "000000", "last_block_id": "000000"}


@given('workspace "W" contains a parsed document', target_fixture="workspace_id")
def _workspace_with_document(bdd_client, bdd_state):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", _DOCUMENT_TEXT.encode(), "text/plain")},
    )
    bdd_state["W"] = workspace_id
    return workspace_id


@given("the user is reading with a known viewport")
def _known_viewport():
    # The concrete viewport block IDs are supplied by each scenario's own
    # request below; nothing to set up ahead of time (ephemeral client
    # state, like passage-marking.feature's marking gesture).
    pass


@scenario(FEATURE, "Starting a discussion from a suggested question")
def test_starting_a_discussion_from_a_suggested_question():
    pass


@given("the user has marked a passage and suggestions are shown")
def _marked_passage_with_suggestions():
    pass


@when(
    "the user picks one of the suggested questions", target_fixture="discussion_response"
)
def _pick_suggested_question(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={
            "message": "What does the categorical imperative mean?",
            "viewport": _VIEWPORT,
            "anchor": _anchor_for("The categorical imperative is Kant's central moral principle."),
        },
    )


@then(
    parsers.parse(
        'a new discussion anchored to that passage is created in workspace "W" in a single '
        "request that carries the suggestion text as the first user message"
    )
)
def _discussion_anchored_with_suggestion_text(discussion_response):
    assert discussion_response.status_code == 201
    body = discussion_response.json()
    assert body["anchor"]["text"] == "The categorical imperative is Kant's central moral principle."
    assert body["turns"][0]["user_message"] == "What does the categorical imperative mean?"


@then("the created discussion contains the completed first turn")
def _discussion_contains_completed_first_turn(discussion_response):
    turns = discussion_response.json()["turns"]
    assert len(turns) == 1
    assert turns[0]["agent_response"]


@scenario(FEATURE, "Starting a discussion with a typed question")
def test_starting_a_discussion_with_a_typed_question():
    pass


@given("the user has marked a passage")
def _user_marked_a_passage():
    pass


@when("the user types their own question and sends it", target_fixture="discussion_response")
def _type_and_send_question(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={
            "message": "Why did Kant frame it this way?",
            "viewport": _VIEWPORT,
            "anchor": _anchor_for("The categorical imperative is Kant's central moral principle."),
        },
    )


@then(
    "a new discussion anchored to that passage is created in a single request that carries "
    "the typed question as the first user message"
)
def _discussion_anchored_with_typed_text(discussion_response):
    assert discussion_response.status_code == 201
    body = discussion_response.json()
    assert body["turns"][0]["user_message"] == "Why did Kant frame it this way?"


@scenario(FEATURE, "Completed turns are persisted")
def test_completed_turns_are_persisted():
    pass


@when("a discussion turn completes", target_fixture="discussion_response")
def _a_discussion_turn_completes(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Tell me more.", "viewport": _VIEWPORT},
    )


@then(
    'the user message, the full agent response, and any tool-call trace are saved as one turn '
    'in the discussion within workspace "W"'
)
def _turn_saved_with_message_response_and_trace(discussion_response, bdd_client, workspace_id):
    assert discussion_response.status_code == 201
    discussion_id = discussion_response.json()["discussion_id"]
    fetched = bdd_client.get(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}"
    ).json()
    assert len(fetched["turns"]) == 1
    turn = fetched["turns"][0]
    assert turn["user_message"] == "Tell me more."
    assert turn["agent_response"]
    assert "tool_calls" in turn


@then("the turn is available as context for all future turns")
def _turn_available_for_future_turns(discussion_response, bdd_client, workspace_id):
    # This discussion's own continuation is carried by the agent's managed
    # session (agent-contract.yaml's discussion_agent.session) — not
    # backend-observable from here (discussion-agent's own bdd/eval suite
    # covers that). What the backend can and does guarantee: the turn is
    # durably retrievable, and a *later* discussion in this workspace picks
    # it up via discussion_history (workspace_history).
    discussion_id = discussion_response.json()["discussion_id"]
    assert bdd_client.get(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}"
    ).status_code == 200


@scenario(FEATURE, "No discussion without a document")
def test_no_discussion_without_a_document():
    pass


@given("a workspace with no document uploaded", target_fixture="workspace_id")
def _workspace_without_document(bdd_client):
    return bdd_client.post("/api/workspaces").json()["workspace_id"]


@then("the UI offers no way to start a discussion")
def _ui_offers_no_way():
    # Frontend rendering concern, out of scope for this backend-only binding.
    pass


@then("API attempts to create a discussion are rejected")
def _api_rejects_discussion_creation(bdd_client, workspace_id):
    response = bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _VIEWPORT},
    )
    assert response.status_code == 409


@scenario(FEATURE, "Agent failure surfaces cleanly")
def test_agent_failure_surfaces_cleanly():
    pass


@given("the agent runtime returns an error mid-turn", target_fixture="workspace_id")
def _agent_runtime_errors(bdd_client, bdd_discussion_agent_client):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", _DOCUMENT_TEXT.encode(), "text/plain")},
    )
    bdd_discussion_agent_client.raise_on_run_turn = True
    return workspace_id


@when("the failure occurs", target_fixture="discussion_response")
def _the_failure_occurs(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _VIEWPORT},
    )


@then("the user sees a clear error state with a retry option")
def _user_sees_clear_error_state(discussion_response):
    assert discussion_response.status_code == 502


@then("no partial turn is persisted to the discussion history")
def _no_partial_turn_persisted(bdd_client, workspace_id):
    assert bdd_client.get(f"/api/workspaces/{workspace_id}/discussions").json() == []

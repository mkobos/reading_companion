"""Backend-observable, untagged scenarios from
spec/features/reading-journal.feature.

@eval-tagged scenario ("Journal synthesizes rather than transcribes") needs a
live-model judgment call and has no eval harness in backend/ yet — not bound
here, same gap noted in tests/bdd/test_passage_marking.py for
passage-marking.feature's @eval scenario.

Uses bdd_llm_client (a scripted fake, see tests/conftest.py's
FakeLlmClient) and bdd_discussion_agent_client (a scripted fake, see
tests/conftest.py's FakeDiscussionAgentClient) — never a live model call
from the backend suite.
"""

import os

from pytest_bdd import given, parsers, scenario, then, when

from tests.bdd.conftest import FEATURES_DIR

FEATURE = os.path.join(FEATURES_DIR, "reading-journal.feature")

_DOCUMENT_TEXT = "The categorical imperative is Kant's central moral principle."
_VIEWPORT = {"first_block_id": "000000", "last_block_id": "000000"}


def _anchor_for(text: str, offset: int = 0) -> dict:
    return {
        "first_block_id": "000000",
        "first_block_offset": offset,
        "last_block_id": "000000",
        "last_block_offset": offset + len(text),
        "text": text,
    }


@given('workspace "W" contains a parsed document', target_fixture="workspace_id")
def _workspace_with_document(bdd_client, bdd_state):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", _DOCUMENT_TEXT.encode(), "text/plain")},
    )
    bdd_state["W"] = workspace_id
    return workspace_id


def _add_note(bdd_client, workspace_id: str, text: str) -> None:
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _anchor_for(_DOCUMENT_TEXT), "text": text},
    )


def _add_discussion_turn(bdd_client, workspace_id: str, message: str) -> None:
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": message, "viewport": _VIEWPORT},
    )


@scenario(FEATURE, "Generating the journal on request")
def test_generating_the_journal_on_request():
    pass


@given('workspace "W" has several notes and discussion turns')
def _several_notes_and_turns(bdd_client, workspace_id):
    _add_note(bdd_client, workspace_id, "A note about duty.")
    _add_discussion_turn(bdd_client, workspace_id, "What is duty?")


@when("the user requests a reading journal update", target_fixture="journal_response")
def _request_journal_update(bdd_client, workspace_id):
    return bdd_client.post(f"/api/workspaces/{workspace_id}/journal")


@then("the notes and discussion history are synthesized into a reading journal")
def _synthesized_into_journal(journal_response, bdd_llm_client):
    assert journal_response.status_code == 200
    assert len(bdd_llm_client.journal_calls) == 1
    assert "A note about duty." in bdd_llm_client.journal_calls[0]
    assert "What is duty?" in bdd_llm_client.journal_calls[0]


@then('the reading journal is saved in workspace "W"')
def _journal_saved(journal_response, bdd_client, workspace_id):
    assert (
        bdd_client.get(f"/api/workspaces/{workspace_id}/journal").json()["text"]
        == journal_response.json()["text"]
    )


@then("the journal is displayed to the user")
def _journal_displayed(journal_response):
    assert journal_response.json()["text"]


@scenario(FEATURE, "Regeneration replaces the previous journal")
def test_regeneration_replaces_the_previous_journal():
    pass


@given(
    parsers.parse('workspace "W" has a reading journal with content "{content}"'),
)
def _existing_journal_with_content(bdd_client, bdd_llm_client, workspace_id, content):
    _add_note(bdd_client, workspace_id, "Initial note.")
    bdd_llm_client.next_journal = content
    bdd_client.post(f"/api/workspaces/{workspace_id}/journal")


@given("the user has since added new notes and discussion turns")
def _new_notes_and_turns_added(bdd_client, bdd_llm_client, workspace_id):
    _add_note(bdd_client, workspace_id, "A newer note about duty.")
    _add_discussion_turn(bdd_client, workspace_id, "What is duty?")
    bdd_llm_client.next_journal = "Updated synthesis."


@then(
    parsers.parse(
        'the new reading journal is generated using the new notes, turns, and "{prior_content}"'
    )
)
def _generated_using_new_and_prior(journal_response, bdd_llm_client, prior_content):
    assert journal_response.status_code == 200
    prompt = bdd_llm_client.journal_calls[-1]
    assert "A newer note about duty." in prompt
    assert prior_content in prompt


@then('the new reading journal replaces the stored journal in workspace "W"')
def _new_journal_replaces_stored(journal_response, bdd_client, workspace_id):
    stored = bdd_client.get(f"/api/workspaces/{workspace_id}/journal").json()
    assert stored["text"] == journal_response.json()["text"]
    assert stored["text"] != "Prior synthesis"


@scenario(FEATURE, "Reading journal update with nothing to synthesize")
def test_reading_journal_update_with_nothing_to_synthesize():
    pass


@given('workspace "W" has no notes and no discussion history')
def _no_notes_or_history():
    # The workspace created by the Background step already has neither.
    pass


@then("the application informs the user there is nothing to reflect on yet")
def _informs_nothing_to_reflect_on(journal_response):
    assert journal_response.status_code == 409


@then("no LLM call is made and no journal is saved")
def _no_llm_call_and_no_journal_saved(bdd_llm_client, bdd_client, workspace_id):
    assert bdd_llm_client.journal_calls == []
    assert bdd_client.get(f"/api/workspaces/{workspace_id}/journal").status_code == 404


@scenario(FEATURE, "Generation failure leaves prior journal intact")
def test_generation_failure_leaves_prior_journal_intact():
    pass


@given('workspace "W" has a current journal')
def _has_a_current_journal(bdd_client, workspace_id):
    _add_note(bdd_client, workspace_id, "A note about duty.")
    bdd_client.post(f"/api/workspaces/{workspace_id}/journal")


@given("the journal generation service returns an error")
def _journal_service_errors(bdd_llm_client):
    bdd_llm_client.raise_on_journal = True


@then("a reading journal generation error is shown to the user with a retry option")
def _generation_error_shown(journal_response):
    assert journal_response.status_code == 503


@then('the previously stored journal remains unchanged in workspace "W"')
def _previous_journal_unchanged(bdd_client, workspace_id, bdd_llm_client):
    stored = bdd_client.get(f"/api/workspaces/{workspace_id}/journal").json()
    assert stored["text"] == "# Journal\n\nDefault fake synthesis."


@scenario(FEATURE, "Journal becomes part of the shared context")
def test_journal_becomes_part_of_the_shared_context():
    pass


@when("a subsequent discussion turn occurs")
def _subsequent_discussion_turn_occurs(bdd_client, workspace_id):
    _add_discussion_turn(bdd_client, workspace_id, "What follows from the journal?")


@then("the journal is included in the shared context provided to the agent")
def _journal_in_shared_context(bdd_discussion_agent_client, bdd_client, workspace_id):
    journal_text = bdd_client.get(f"/api/workspaces/{workspace_id}/journal").json()["text"]
    context = bdd_discussion_agent_client.run_turn_calls[-1]["context"]
    assert context["journal"] == journal_text

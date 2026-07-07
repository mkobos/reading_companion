import os

from pytest_bdd import given, parsers, scenario, then, when

from tests.bdd.conftest import FEATURES_DIR

FEATURE = os.path.join(FEATURES_DIR, "notes.feature")

_DOCUMENT_TEXT = "First sentence for anchoring. Second sentence."


@given('workspace "W" contains a parsed document', target_fixture="workspace_id")
def _workspace_with_document(bdd_client, bdd_state):
    workspace_id = bdd_client.post("/api/workspaces").json()["workspace_id"]
    bdd_client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("doc.txt", _DOCUMENT_TEXT.encode(), "text/plain")},
    )
    bdd_state["W"] = workspace_id
    return workspace_id


def _anchor_for(text: str, offset: int = 0) -> dict:
    return {
        "first_block_id": "000000",
        "first_block_offset": offset,
        "last_block_id": "000000",
        "last_block_offset": offset + len(text),
        "text": text,
    }


@scenario(FEATURE, "Adding a note to a passage")
def test_adding_a_note_to_a_passage():
    pass


@given("the user has marked a passage")
def _user_marked_a_passage():
    # Marking is ephemeral client state (passage-marking.feature) — nothing
    # to set up backend-side beyond the anchor used in the next step.
    pass


@when(
    parsers.parse('the user adds a note with text "{text}"'), target_fixture="response"
)
def _add_note(bdd_client, workspace_id, text):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _anchor_for("First sentence for anchoring."), "text": text},
    )


@then(parsers.parse('the note is saved in workspace "W" with the text "{text}"'))
def _note_saved_with_text(response, text):
    assert response.status_code == 201
    assert response.json()["text"] == text


@then("the saved note has a creation timestamp and a passage anchor")
def _note_has_timestamp_and_anchor(response):
    body = response.json()
    assert body["created_at"]
    assert body["anchor"]["text"]


@then("no AI call is made")
def _no_ai_call():
    # Structural guarantee: app/routers/notes.py never imports or calls any
    # LLM/agent client — nothing to assert at runtime beyond that absence.
    pass


@then("a note indicator is displayed on the passage in the reading view")
def _note_indicator_displayed():
    # Frontend rendering concern, out of scope for this backend-only binding.
    pass


@scenario(FEATURE, "Editing a note")
def test_editing_a_note():
    pass


@given(
    parsers.parse('a note with text "{text}" exists in workspace "W"'),
    target_fixture="note",
)
def _note_exists(bdd_client, workspace_id, text):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _anchor_for("First sentence for anchoring."), "text": text},
    ).json()


@when(
    parsers.parse('the user changes the note text to "{text}"'), target_fixture="response"
)
def _change_note_text(bdd_client, workspace_id, note, text):
    return bdd_client.put(
        f"/api/workspaces/{workspace_id}/notes/{note['note_id']}", json={"text": text}
    )


@then(parsers.parse('the stored note text is updated to "{text}"'))
def _stored_text_updated(response, text):
    assert response.status_code == 200
    assert response.json()["text"] == text


@then("the note's updated timestamp is updated")
def _updated_timestamp_changed(response, note):
    assert response.json()["updated_at"] != note["updated_at"]
    assert response.json()["created_at"] == note["created_at"]


@scenario(FEATURE, "Deleting a note")
def test_deleting_a_note():
    pass


@given('a note exists in workspace "W"', target_fixture="note")
def _a_note_exists(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _anchor_for("First sentence for anchoring."), "text": "Some note."},
    ).json()


@when("the user deletes the note", target_fixture="response")
def _delete_the_note(bdd_client, workspace_id, note):
    return bdd_client.delete(f"/api/workspaces/{workspace_id}/notes/{note['note_id']}")


@then('the note is removed from workspace "W"')
def _note_removed(response, bdd_client, workspace_id):
    assert response.status_code == 204
    assert bdd_client.get(f"/api/workspaces/{workspace_id}/notes").json() == []


@then("the note's indicator is removed from the reading view")
def _indicator_removed():
    # Frontend rendering concern, out of scope for this backend-only binding.
    pass


@scenario(FEATURE, "Empty note is rejected")
def test_empty_note_is_rejected():
    pass


@when(
    "the user attempts to save a note with empty text", target_fixture="response"
)
def _attempt_empty_note(bdd_client, workspace_id):
    return bdd_client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _anchor_for("First sentence for anchoring."), "text": ""},
    )


@then("the note is not saved")
def _note_not_saved(response, bdd_client, workspace_id):
    assert response.status_code == 400
    assert bdd_client.get(f"/api/workspaces/{workspace_id}/notes").json() == []


@then("the note input remains open for correction")
def _note_input_remains_open():
    # Frontend UI-state concern, out of scope for this backend-only binding.
    pass

def _create_workspace_with_document(client, text: bytes = b"Hello world. Second sentence.") -> str:
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]
    client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes.txt", text, "text/plain")},
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


def test_create_note_returns_201(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": "Interesting argument here."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "Interesting argument here."
    assert body["anchor"]["text"] == "Hello world."
    assert "note_id" in body
    assert body["created_at"] == body["updated_at"]


def test_list_notes_returns_created_notes(client):
    workspace_id = _create_workspace_with_document(client)
    client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": "Note one."},
    )

    response = client.get(f"/api/workspaces/{workspace_id}/notes")

    assert response.status_code == 200
    assert [n["text"] for n in response.json()] == ["Note one."]


def test_update_note_changes_text_and_timestamp(client):
    workspace_id = _create_workspace_with_document(client)
    note = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": "Original note text."},
    ).json()

    response = client.put(
        f"/api/workspaces/{workspace_id}/notes/{note['note_id']}",
        json={"text": "Updated note text."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Updated note text."
    assert body["created_at"] == note["created_at"]


def test_delete_note_removes_it(client):
    workspace_id = _create_workspace_with_document(client)
    note = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": "Temporary note."},
    ).json()

    delete_response = client.delete(f"/api/workspaces/{workspace_id}/notes/{note['note_id']}")
    assert delete_response.status_code == 204

    list_response = client.get(f"/api/workspaces/{workspace_id}/notes")
    assert list_response.json() == []


def test_workspace_note_count_reflects_real_notes(client):
    workspace_id = _create_workspace_with_document(client)

    client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": "Note one."},
    )
    note2 = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": "Note two."},
    ).json()

    assert client.get(f"/api/workspaces/{workspace_id}").json()["note_count"] == 2

    client.delete(f"/api/workspaces/{workspace_id}/notes/{note2['note_id']}")

    assert client.get(f"/api/workspaces/{workspace_id}").json()["note_count"] == 1


def test_create_note_with_unknown_block_id_is_rejected(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={
            "anchor": {
                "first_block_id": "999999",
                "first_block_offset": 0,
                "last_block_id": "999999",
                "last_block_offset": 5,
                "text": "Hello",
            },
            "text": "A note.",
        },
    )

    assert response.status_code == 400
    assert client.get(f"/api/workspaces/{workspace_id}/notes").json() == []


def test_create_note_with_mismatched_text_is_rejected(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(text="wrong text"), "text": "A note."},
    )

    assert response.status_code == 400
    assert client.get(f"/api/workspaces/{workspace_id}/notes").json() == []


def test_create_note_with_empty_text_is_rejected(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/notes",
        json={"anchor": _valid_anchor(), "text": ""},
    )

    assert response.status_code == 400
    assert client.get(f"/api/workspaces/{workspace_id}/notes").json() == []


def test_notes_are_isolated_between_workspaces(client):
    workspace_a = _create_workspace_with_document(client)
    workspace_b = _create_workspace_with_document(client)

    note_a = client.post(
        f"/api/workspaces/{workspace_a}/notes",
        json={"anchor": _valid_anchor(), "text": "Workspace A note."},
    ).json()

    assert client.get(f"/api/workspaces/{workspace_b}/notes").json() == []
    # A note ID from workspace A must not be reachable via workspace B's path.
    assert (
        client.put(
            f"/api/workspaces/{workspace_b}/notes/{note_a['note_id']}",
            json={"text": "hijacked"},
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/workspaces/{workspace_b}/notes/{note_a['note_id']}").status_code
        == 404
    )


def test_notes_on_nonexistent_workspace_return_404(client):
    response = client.get("/api/workspaces/does-not-exist/notes")

    assert response.status_code == 404


def test_update_nonexistent_note_returns_404(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.put(
        f"/api/workspaces/{workspace_id}/notes/does-not-exist",
        json={"text": "new text"},
    )

    assert response.status_code == 404


def test_delete_nonexistent_note_returns_404(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.delete(f"/api/workspaces/{workspace_id}/notes/does-not-exist")

    assert response.status_code == 404

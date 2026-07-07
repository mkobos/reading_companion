"""Integration tests for FirestoreStore against the real Firestore emulator.

Skipped (not deleted, not mocked) if FIRESTORE_EMULATOR_HOST isn't set or
the emulator isn't reachable at that address (e.g. no JRE on PATH). To run
these for real:

    export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"   # if java isn't on PATH
    gcloud emulators firestore start --host-port=localhost:8080 &
    export FIRESTORE_EMULATOR_HOST=localhost:8080
    uv run pytest tests/integration

See docs/repo_configuration_progress.md for when/why this was set up.
"""

import os
import socket
from datetime import datetime, timezone

import pytest

from app.parsing import Block
from app.passages import Passage
from app.store import (
    Document,
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    Note,
    NoteNotFoundError,
    Workspace,
    WorkspaceNotFoundError,
)
from app.store.firestore_store import FirestoreStore


def _emulator_reachable() -> bool:
    host_port = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if not host_port:
        return False
    host, _, port = host_port.partition(":")
    try:
        with socket.create_connection((host, int(port or 8080)), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _emulator_reachable(),
    reason="FIRESTORE_EMULATOR_HOST not set or emulator unreachable "
    "(requires a JRE + `gcloud emulators firestore start`; unavailable in "
    "this sandbox, see docs/repo_configuration_progress.md)",
)


@pytest.fixture
def store() -> FirestoreStore:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    return FirestoreStore()


def test_create_and_get_workspace(store: FirestoreStore):
    workspace = Workspace(workspace_id="it-ws-1", created_at=datetime.now(timezone.utc))
    store.create_workspace(workspace)

    fetched = store.get_workspace("it-ws-1")

    assert fetched.workspace_id == "it-ws-1"
    store.delete_workspace("it-ws-1")


def test_get_missing_workspace_raises(store: FirestoreStore):
    with pytest.raises(WorkspaceNotFoundError):
        store.get_workspace("does-not-exist")


def test_document_lifecycle_and_immutability(store: FirestoreStore):
    workspace = Workspace(workspace_id="it-ws-2", created_at=datetime.now(timezone.utc))
    store.create_workspace(workspace)

    document = Document(
        filename="a.txt",
        format="text",
        size_bytes=5,
        uploaded_at=datetime.now(timezone.utc),
        blocks=[Block(block_id="000000", type="paragraph", text="Hello")],
    )
    store.put_document("it-ws-2", document)

    fetched = store.get_document("it-ws-2")
    assert fetched.blocks[0].text == "Hello"

    with pytest.raises(DocumentAlreadyExistsError):
        store.put_document("it-ws-2", document)

    store.delete_workspace("it-ws-2")
    with pytest.raises(WorkspaceNotFoundError):
        store.get_document("it-ws-2")


def test_recursive_delete_removes_document_subcollection(store: FirestoreStore):
    workspace = Workspace(workspace_id="it-ws-3", created_at=datetime.now(timezone.utc))
    store.create_workspace(workspace)
    store.put_document(
        "it-ws-3",
        Document(
            filename="a.txt",
            format="text",
            size_bytes=5,
            uploaded_at=datetime.now(timezone.utc),
            blocks=[],
        ),
    )

    store.delete_workspace("it-ws-3")
    with pytest.raises(WorkspaceNotFoundError):
        store.get_document("it-ws-3")

    # Recreating the workspace under the same ID must not resurrect the
    # deleted document subcollection.
    store.create_workspace(workspace)
    with pytest.raises(DocumentNotFoundError):
        store.get_document("it-ws-3")
    store.delete_workspace("it-ws-3")


def test_note_lifecycle_and_workspace_scoping(store: FirestoreStore):
    workspace_a = Workspace(workspace_id="it-ws-4a", created_at=datetime.now(timezone.utc))
    workspace_b = Workspace(workspace_id="it-ws-4b", created_at=datetime.now(timezone.utc))
    store.create_workspace(workspace_a)
    store.create_workspace(workspace_b)

    now = datetime.now(timezone.utc)
    note = Note(
        note_id="it-note-1",
        anchor=Passage(
            first_block_id="000000",
            first_block_offset=0,
            last_block_id="000000",
            last_block_offset=5,
            text="Hello",
        ),
        text="Original text.",
        created_at=now,
        updated_at=now,
    )
    store.create_note("it-ws-4a", note)

    assert [n.note_id for n in store.list_notes("it-ws-4a")] == ["it-note-1"]
    assert store.list_notes("it-ws-4b") == []

    updated_at = datetime.now(timezone.utc)
    updated = store.update_note("it-ws-4a", "it-note-1", text="Updated text.", updated_at=updated_at)
    assert updated.text == "Updated text."
    assert store.get_note("it-ws-4a", "it-note-1").text == "Updated text."

    with pytest.raises(NoteNotFoundError):
        store.get_note("it-ws-4b", "it-note-1")

    store.delete_note("it-ws-4a", "it-note-1")
    with pytest.raises(NoteNotFoundError):
        store.get_note("it-ws-4a", "it-note-1")

    store.delete_workspace("it-ws-4a")
    store.delete_workspace("it-ws-4b")

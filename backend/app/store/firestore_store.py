"""Real WorkspaceStore, per spec/contracts/data-model.yaml's
firestore_mapping. Exercised by tests/integration/test_firestore_store.py
against the Firestore emulator (see that file for why it's skip-gated in
this sandbox)."""

from dataclasses import replace
from datetime import datetime, timezone

from google.cloud import firestore

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

_WORKSPACES_COLLECTION = "workspaces"
_DOCUMENT_SUBCOLLECTION = "document"
_DOCUMENT_DOC_ID = "current"
_NOTES_SUBCOLLECTION = "notes"


class FirestoreStore:
    def __init__(self, client: firestore.Client | None = None) -> None:
        self._client = client or firestore.Client()

    def _workspace_ref(self, workspace_id: str):
        return self._client.collection(_WORKSPACES_COLLECTION).document(workspace_id)

    def create_workspace(self, workspace: Workspace) -> None:
        self._workspace_ref(workspace.workspace_id).set(
            {
                "created_at": workspace.created_at,
                "last_accessed_at": workspace.last_accessed_at,
            }
        )

    def get_workspace(self, workspace_id: str) -> Workspace:
        ref = self._workspace_ref(workspace_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise WorkspaceNotFoundError(workspace_id)
        now = datetime.now(timezone.utc)
        ref.update({"last_accessed_at": now})
        data = snapshot.to_dict()
        return Workspace(
            workspace_id=workspace_id,
            created_at=data["created_at"],
            last_accessed_at=now,
        )

    def delete_workspace(self, workspace_id: str) -> None:
        # Firestore document deletion does not cascade to subcollections
        # (data-model.yaml firestore_mapping) — walk and delete explicitly.
        ref = self._workspace_ref(workspace_id)
        for subcollection in ref.collections():
            for doc in subcollection.stream():
                self._delete_document_recursive(doc.reference)
        ref.delete()

    def _delete_document_recursive(self, doc_ref) -> None:
        for subcollection in doc_ref.collections():
            for doc in subcollection.stream():
                self._delete_document_recursive(doc.reference)
        doc_ref.delete()

    def put_document(self, workspace_id: str, document: Document) -> None:
        workspace_ref = self._workspace_ref(workspace_id)
        if not workspace_ref.get().exists:
            raise WorkspaceNotFoundError(workspace_id)
        doc_ref = workspace_ref.collection(_DOCUMENT_SUBCOLLECTION).document(
            _DOCUMENT_DOC_ID
        )
        if doc_ref.get().exists:
            raise DocumentAlreadyExistsError(workspace_id)
        doc_ref.set(
            {
                "filename": document.filename,
                "format": document.format,
                "size_bytes": document.size_bytes,
                "uploaded_at": document.uploaded_at,
                "blocks": [
                    {
                        "block_id": b.block_id,
                        "type": b.type,
                        "text": b.text,
                        "level": b.level,
                    }
                    for b in document.blocks
                ],
            }
        )

    def get_document(self, workspace_id: str) -> Document:
        workspace_ref = self._workspace_ref(workspace_id)
        if not workspace_ref.get().exists:
            raise WorkspaceNotFoundError(workspace_id)
        doc_ref = workspace_ref.collection(_DOCUMENT_SUBCOLLECTION).document(
            _DOCUMENT_DOC_ID
        )
        snapshot = doc_ref.get()
        if not snapshot.exists:
            raise DocumentNotFoundError(workspace_id)
        data = snapshot.to_dict()
        blocks = [
            Block(
                block_id=b["block_id"], type=b["type"], text=b["text"], level=b.get("level")
            )
            for b in data["blocks"]
        ]
        return Document(
            filename=data["filename"],
            format=data["format"],
            size_bytes=data["size_bytes"],
            uploaded_at=data["uploaded_at"],
            blocks=blocks,
        )

    def has_document(self, workspace_id: str) -> bool:
        workspace_ref = self._workspace_ref(workspace_id)
        doc_ref = workspace_ref.collection(_DOCUMENT_SUBCOLLECTION).document(
            _DOCUMENT_DOC_ID
        )
        return doc_ref.get().exists

    def _notes_collection(self, workspace_id: str):
        return self._workspace_ref(workspace_id).collection(_NOTES_SUBCOLLECTION)

    def _require_workspace(self, workspace_id: str) -> None:
        if not self._workspace_ref(workspace_id).get().exists:
            raise WorkspaceNotFoundError(workspace_id)

    @staticmethod
    def _note_to_dict(note: Note) -> dict:
        anchor = note.anchor
        return {
            "anchor": {
                "first_block_id": anchor.first_block_id,
                "first_block_offset": anchor.first_block_offset,
                "last_block_id": anchor.last_block_id,
                "last_block_offset": anchor.last_block_offset,
                "text": anchor.text,
            },
            "text": note.text,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
        }

    @staticmethod
    def _note_from_dict(note_id: str, data: dict) -> Note:
        anchor_data = data["anchor"]
        return Note(
            note_id=note_id,
            anchor=Passage(
                first_block_id=anchor_data["first_block_id"],
                first_block_offset=anchor_data["first_block_offset"],
                last_block_id=anchor_data["last_block_id"],
                last_block_offset=anchor_data["last_block_offset"],
                text=anchor_data["text"],
            ),
            text=data["text"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def create_note(self, workspace_id: str, note: Note) -> None:
        self._require_workspace(workspace_id)
        self._notes_collection(workspace_id).document(note.note_id).set(
            self._note_to_dict(note)
        )

    def list_notes(self, workspace_id: str) -> list[Note]:
        self._require_workspace(workspace_id)
        docs = self._notes_collection(workspace_id).order_by("created_at").stream()
        return [self._note_from_dict(doc.id, doc.to_dict()) for doc in docs]

    def get_note(self, workspace_id: str, note_id: str) -> Note:
        self._require_workspace(workspace_id)
        snapshot = self._notes_collection(workspace_id).document(note_id).get()
        if not snapshot.exists:
            raise NoteNotFoundError(note_id)
        return self._note_from_dict(note_id, snapshot.to_dict())

    def update_note(self, workspace_id: str, note_id: str, text: str, updated_at) -> Note:
        note = self.get_note(workspace_id, note_id)
        self._notes_collection(workspace_id).document(note_id).update(
            {"text": text, "updated_at": updated_at}
        )
        return replace(note, text=text, updated_at=updated_at)

    def delete_note(self, workspace_id: str, note_id: str) -> None:
        self._require_workspace(workspace_id)
        self._notes_collection(workspace_id).document(note_id).delete()

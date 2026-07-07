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
    Discussion,
    DiscussionNotFoundError,
    Document,
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    Note,
    NoteNotFoundError,
    ToolCall,
    Turn,
    Workspace,
    WorkspaceNotFoundError,
)
from app.viewport import Viewport

_WORKSPACES_COLLECTION = "workspaces"
_DOCUMENT_SUBCOLLECTION = "document"
_DOCUMENT_DOC_ID = "current"
_NOTES_SUBCOLLECTION = "notes"
_DISCUSSIONS_SUBCOLLECTION = "discussions"
_TURNS_SUBCOLLECTION = "turns"


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

    def _discussions_collection(self, workspace_id: str):
        return self._workspace_ref(workspace_id).collection(_DISCUSSIONS_SUBCOLLECTION)

    def _turns_collection(self, workspace_id: str, discussion_id: str):
        return self._discussions_collection(workspace_id).document(discussion_id).collection(
            _TURNS_SUBCOLLECTION
        )

    @staticmethod
    def _discussion_to_dict(discussion: Discussion) -> dict:
        anchor = discussion.anchor
        return {
            "anchor": (
                {
                    "first_block_id": anchor.first_block_id,
                    "first_block_offset": anchor.first_block_offset,
                    "last_block_id": anchor.last_block_id,
                    "last_block_offset": anchor.last_block_offset,
                    "text": anchor.text,
                }
                if anchor is not None
                else None
            ),
            "created_at": discussion.created_at,
            "turn_count": discussion.turn_count,
            "first_message_preview": discussion.first_message_preview,
        }

    @staticmethod
    def _discussion_from_dict(discussion_id: str, data: dict) -> Discussion:
        anchor_data = data.get("anchor")
        anchor = (
            Passage(
                first_block_id=anchor_data["first_block_id"],
                first_block_offset=anchor_data["first_block_offset"],
                last_block_id=anchor_data["last_block_id"],
                last_block_offset=anchor_data["last_block_offset"],
                text=anchor_data["text"],
            )
            if anchor_data is not None
            else None
        )
        return Discussion(
            discussion_id=discussion_id,
            created_at=data["created_at"],
            turn_count=data["turn_count"],
            first_message_preview=data["first_message_preview"],
            anchor=anchor,
        )

    @staticmethod
    def _turn_to_dict(turn: Turn) -> dict:
        return {
            "user_message": turn.user_message,
            "agent_response": turn.agent_response,
            "viewport": {
                "first_block_id": turn.viewport.first_block_id,
                "last_block_id": turn.viewport.last_block_id,
            },
            "tool_calls": [
                {
                    "tool": tc.tool,
                    "input_summary": tc.input_summary,
                    "result_summary": tc.result_summary,
                }
                for tc in turn.tool_calls
            ],
            "created_at": turn.created_at,
        }

    @staticmethod
    def _turn_from_dict(turn_id: str, data: dict) -> Turn:
        viewport_data = data["viewport"]
        return Turn(
            turn_id=turn_id,
            user_message=data["user_message"],
            agent_response=data["agent_response"],
            viewport=Viewport(
                first_block_id=viewport_data["first_block_id"],
                last_block_id=viewport_data["last_block_id"],
            ),
            created_at=data["created_at"],
            tool_calls=[
                ToolCall(
                    tool=tc["tool"],
                    input_summary=tc["input_summary"],
                    result_summary=tc.get("result_summary"),
                )
                for tc in data.get("tool_calls", [])
            ],
        )

    def create_discussion(self, workspace_id: str, discussion: Discussion, first_turn: Turn) -> None:
        self._require_workspace(workspace_id)
        batch = self._client.batch()
        discussion_ref = self._discussions_collection(workspace_id).document(discussion.discussion_id)
        batch.set(discussion_ref, self._discussion_to_dict(discussion))
        turn_ref = discussion_ref.collection(_TURNS_SUBCOLLECTION).document(first_turn.turn_id)
        batch.set(turn_ref, self._turn_to_dict(first_turn))
        batch.commit()

    def list_discussions(self, workspace_id: str) -> list[Discussion]:
        self._require_workspace(workspace_id)
        docs = self._discussions_collection(workspace_id).order_by("created_at").stream()
        return [self._discussion_from_dict(doc.id, doc.to_dict()) for doc in docs]

    def get_discussion(self, workspace_id: str, discussion_id: str) -> tuple[Discussion, list[Turn]]:
        self._require_workspace(workspace_id)
        snapshot = self._discussions_collection(workspace_id).document(discussion_id).get()
        if not snapshot.exists:
            raise DiscussionNotFoundError(discussion_id)
        discussion = self._discussion_from_dict(discussion_id, snapshot.to_dict())
        turn_docs = self._turns_collection(workspace_id, discussion_id).order_by("created_at").stream()
        turns = [self._turn_from_dict(doc.id, doc.to_dict()) for doc in turn_docs]
        return discussion, turns

    def append_turn(self, workspace_id: str, discussion_id: str, turn: Turn) -> None:
        self._require_workspace(workspace_id)
        discussion_ref = self._discussions_collection(workspace_id).document(discussion_id)
        if not discussion_ref.get().exists:
            raise DiscussionNotFoundError(discussion_id)
        batch = self._client.batch()
        turn_ref = discussion_ref.collection(_TURNS_SUBCOLLECTION).document(turn.turn_id)
        batch.set(turn_ref, self._turn_to_dict(turn))
        batch.update(discussion_ref, {"turn_count": firestore.Increment(1)})
        batch.commit()

    def list_recent_turns(
        self, workspace_id: str, *, exclude_discussion_id: str, limit: int
    ) -> list[Turn]:
        # Fan-out over this workspace's discussions rather than a Firestore
        # collection-group query, per data-model.yaml's "no collection-group
        # queries" invariant (cross-workspace leakage impossible by
        # construction, not by a filter that could be forgotten).
        self._require_workspace(workspace_id)
        candidates: list[Turn] = []
        for discussion_doc in self._discussions_collection(workspace_id).stream():
            if discussion_doc.id == exclude_discussion_id:
                continue
            turn_docs = (
                self._turns_collection(workspace_id, discussion_doc.id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            candidates.extend(self._turn_from_dict(doc.id, doc.to_dict()) for doc in turn_docs)
        candidates.sort(key=lambda t: t.created_at, reverse=True)
        return candidates[:limit]

    def count_discussions(self, workspace_id: str) -> int:
        self._require_workspace(workspace_id)
        aggregation = self._discussions_collection(workspace_id).count().get()
        return int(aggregation[0][0].value)

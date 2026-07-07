from dataclasses import replace
from datetime import datetime, timezone

from app.store import (
    Document,
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    Note,
    NoteNotFoundError,
    Workspace,
    WorkspaceNotFoundError,
)


class InMemoryWorkspaceStore:
    """Test double for WorkspaceStore. Not for production use."""

    def __init__(self) -> None:
        self._workspaces: dict[str, Workspace] = {}
        self._documents: dict[str, Document] = {}
        self._notes: dict[str, dict[str, Note]] = {}

    def create_workspace(self, workspace: Workspace) -> None:
        self._workspaces[workspace.workspace_id] = workspace

    def get_workspace(self, workspace_id: str) -> Workspace:
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(workspace_id)
        workspace = replace(workspace, last_accessed_at=datetime.now(timezone.utc))
        self._workspaces[workspace_id] = workspace
        return workspace

    def delete_workspace(self, workspace_id: str) -> None:
        self._workspaces.pop(workspace_id, None)
        self._documents.pop(workspace_id, None)
        self._notes.pop(workspace_id, None)

    def put_document(self, workspace_id: str, document: Document) -> None:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        if workspace_id in self._documents:
            raise DocumentAlreadyExistsError(workspace_id)
        self._documents[workspace_id] = document

    def get_document(self, workspace_id: str) -> Document:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        document = self._documents.get(workspace_id)
        if document is None:
            raise DocumentNotFoundError(workspace_id)
        return document

    def has_document(self, workspace_id: str) -> bool:
        return workspace_id in self._documents

    def create_note(self, workspace_id: str, note: Note) -> None:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        self._notes.setdefault(workspace_id, {})[note.note_id] = note

    def list_notes(self, workspace_id: str) -> list[Note]:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        notes = self._notes.get(workspace_id, {}).values()
        return sorted(notes, key=lambda n: n.created_at)

    def get_note(self, workspace_id: str, note_id: str) -> Note:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        note = self._notes.get(workspace_id, {}).get(note_id)
        if note is None:
            raise NoteNotFoundError(note_id)
        return note

    def update_note(self, workspace_id: str, note_id: str, text: str, updated_at: datetime) -> Note:
        note = self.get_note(workspace_id, note_id)
        updated = replace(note, text=text, updated_at=updated_at)
        self._notes[workspace_id][note_id] = updated
        return updated

    def delete_note(self, workspace_id: str, note_id: str) -> None:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        self._notes.get(workspace_id, {}).pop(note_id, None)

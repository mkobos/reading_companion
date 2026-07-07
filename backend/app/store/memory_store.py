from dataclasses import replace
from datetime import datetime, timezone

from app.store import (
    Discussion,
    DiscussionNotFoundError,
    Document,
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    Journal,
    JournalNotFoundError,
    Note,
    NoteNotFoundError,
    Turn,
    Workspace,
    WorkspaceNotFoundError,
)


class InMemoryWorkspaceStore:
    """Test double for WorkspaceStore. Not for production use."""

    def __init__(self) -> None:
        self._workspaces: dict[str, Workspace] = {}
        self._documents: dict[str, Document] = {}
        self._notes: dict[str, dict[str, Note]] = {}
        self._discussions: dict[str, dict[str, Discussion]] = {}
        self._turns: dict[str, dict[str, list[Turn]]] = {}
        self._journals: dict[str, Journal] = {}

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
        self._discussions.pop(workspace_id, None)
        self._turns.pop(workspace_id, None)
        self._journals.pop(workspace_id, None)

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

    def create_discussion(self, workspace_id: str, discussion: Discussion, first_turn: Turn) -> None:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        self._discussions.setdefault(workspace_id, {})[discussion.discussion_id] = discussion
        self._turns.setdefault(workspace_id, {})[discussion.discussion_id] = [first_turn]

    def list_discussions(self, workspace_id: str) -> list[Discussion]:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        discussions = self._discussions.get(workspace_id, {}).values()
        return sorted(discussions, key=lambda d: d.created_at)

    def get_discussion(self, workspace_id: str, discussion_id: str) -> tuple[Discussion, list[Turn]]:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        discussion = self._discussions.get(workspace_id, {}).get(discussion_id)
        if discussion is None:
            raise DiscussionNotFoundError(discussion_id)
        turns = sorted(
            self._turns.get(workspace_id, {}).get(discussion_id, []), key=lambda t: t.created_at
        )
        return discussion, turns

    def append_turn(self, workspace_id: str, discussion_id: str, turn: Turn) -> None:
        discussion, _ = self.get_discussion(workspace_id, discussion_id)
        self._turns[workspace_id][discussion_id].append(turn)
        self._discussions[workspace_id][discussion_id] = replace(
            discussion, turn_count=discussion.turn_count + 1
        )

    def list_recent_turns(
        self, workspace_id: str, *, exclude_discussion_id: str, limit: int
    ) -> list[Turn]:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        candidates: list[Turn] = []
        for discussion_id, turns in self._turns.get(workspace_id, {}).items():
            if discussion_id == exclude_discussion_id:
                continue
            candidates.extend(sorted(turns, key=lambda t: t.created_at, reverse=True)[:limit])
        candidates.sort(key=lambda t: t.created_at, reverse=True)
        return candidates[:limit]

    def count_discussions(self, workspace_id: str) -> int:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        return len(self._discussions.get(workspace_id, {}))

    def list_all_turns(self, workspace_id: str) -> list[Turn]:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        all_turns = [
            turn for turns in self._turns.get(workspace_id, {}).values() for turn in turns
        ]
        return sorted(all_turns, key=lambda t: t.created_at)

    def put_journal(self, workspace_id: str, journal: Journal) -> None:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        self._journals[workspace_id] = journal

    def get_journal(self, workspace_id: str) -> Journal:
        if workspace_id not in self._workspaces:
            raise WorkspaceNotFoundError(workspace_id)
        journal = self._journals.get(workspace_id)
        if journal is None:
            raise JournalNotFoundError(workspace_id)
        return journal

    def has_journal(self, workspace_id: str) -> bool:
        return workspace_id in self._journals

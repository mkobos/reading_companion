"""Workspace/document persistence port.

Two implementations share this Protocol: `firestore_store.FirestoreStore`
(real, per spec/contracts/data-model.yaml's firestore_mapping) and
`memory_store.InMemoryWorkspaceStore` (test fake). Routers depend only on
this Protocol, never on a concrete implementation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.parsing import Block
from app.passages import Passage
from app.viewport import Viewport


@dataclass(frozen=True)
class Workspace:
    workspace_id: str
    created_at: datetime
    last_accessed_at: datetime | None = None


@dataclass(frozen=True)
class Document:
    filename: str
    format: str  # "text" | "markdown"
    size_bytes: int
    uploaded_at: datetime
    blocks: list[Block] = field(default_factory=list)


@dataclass(frozen=True)
class Note:
    note_id: str
    anchor: Passage
    text: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ToolCall:
    tool: str
    input_summary: str
    result_summary: str | None = None


@dataclass(frozen=True)
class Turn:
    turn_id: str
    user_message: str
    agent_response: str
    viewport: Viewport
    created_at: datetime
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass(frozen=True)
class Discussion:
    discussion_id: str
    created_at: datetime
    turn_count: int
    first_message_preview: str
    anchor: Passage | None = None


@dataclass(frozen=True)
class Journal:
    text: str
    generated_at: datetime


class WorkspaceNotFoundError(Exception):
    pass


class DocumentAlreadyExistsError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class NoteNotFoundError(Exception):
    pass


class DiscussionNotFoundError(Exception):
    pass


class JournalNotFoundError(Exception):
    pass


class WorkspaceStore(Protocol):
    def create_workspace(self, workspace: Workspace) -> None: ...

    def get_workspace(self, workspace_id: str) -> Workspace:
        """Raises WorkspaceNotFoundError if it doesn't exist."""

    def delete_workspace(self, workspace_id: str) -> None:
        """Recursively deletes the workspace and everything under it.
        No-op-safe to call on a nonexistent workspace (idempotent)."""

    def put_document(self, workspace_id: str, document: Document) -> None:
        """Raises WorkspaceNotFoundError or DocumentAlreadyExistsError."""

    def get_document(self, workspace_id: str) -> Document:
        """Raises WorkspaceNotFoundError or DocumentNotFoundError."""

    def has_document(self, workspace_id: str) -> bool: ...

    def create_note(self, workspace_id: str, note: Note) -> None:
        """Raises WorkspaceNotFoundError."""

    def list_notes(self, workspace_id: str) -> list[Note]:
        """Ordered by created_at. Raises WorkspaceNotFoundError."""

    def get_note(self, workspace_id: str, note_id: str) -> Note:
        """Raises WorkspaceNotFoundError or NoteNotFoundError."""

    def update_note(self, workspace_id: str, note_id: str, text: str, updated_at: datetime) -> Note:
        """Raises WorkspaceNotFoundError or NoteNotFoundError."""

    def delete_note(self, workspace_id: str, note_id: str) -> None:
        """Raises WorkspaceNotFoundError. No-op-safe on an unknown note_id
        (idempotent)."""

    def create_discussion(self, workspace_id: str, discussion: Discussion, first_turn: Turn) -> None:
        """Atomically persists a new discussion and its first turn.
        Raises WorkspaceNotFoundError."""

    def list_discussions(self, workspace_id: str) -> list[Discussion]:
        """Ordered by created_at. Raises WorkspaceNotFoundError."""

    def get_discussion(self, workspace_id: str, discussion_id: str) -> tuple[Discussion, list[Turn]]:
        """Turns ordered by created_at. Raises WorkspaceNotFoundError or
        DiscussionNotFoundError."""

    def append_turn(self, workspace_id: str, discussion_id: str, turn: Turn) -> None:
        """Persists `turn` and increments the discussion's turn_count in one
        write. Raises WorkspaceNotFoundError or DiscussionNotFoundError."""

    def list_recent_turns(
        self, workspace_id: str, *, exclude_discussion_id: str, limit: int
    ) -> list[Turn]:
        """The `limit` most recent turns across all discussions in the
        workspace other than `exclude_discussion_id`, newest first.
        Raises WorkspaceNotFoundError."""

    def count_discussions(self, workspace_id: str) -> int:
        """Raises WorkspaceNotFoundError."""

    def list_all_turns(self, workspace_id: str) -> list[Turn]:
        """Every turn across every discussion in the workspace, oldest
        first. Unlike list_recent_turns, no exclusion or limit — used for
        journal synthesis, which needs the full history.
        Raises WorkspaceNotFoundError."""

    def put_journal(self, workspace_id: str, journal: Journal) -> None:
        """Overwrites any existing journal. Raises WorkspaceNotFoundError."""

    def get_journal(self, workspace_id: str) -> Journal:
        """Raises WorkspaceNotFoundError or JournalNotFoundError."""

    def has_journal(self, workspace_id: str) -> bool: ...

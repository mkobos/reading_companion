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


class WorkspaceNotFoundError(Exception):
    pass


class DocumentAlreadyExistsError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class NoteNotFoundError(Exception):
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

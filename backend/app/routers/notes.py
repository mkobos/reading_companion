from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.errors import bad_request_error, not_found_error
from app.ids import generate_note_id
from app.models import NoteCreateRequest, NoteResponse, NoteUpdateRequest, PassageResponse
from app.parsing import Block
from app.passages import Passage, PassageValidationError, validate_passage
from app.store import (
    DocumentNotFoundError,
    Note,
    NoteNotFoundError,
    WorkspaceNotFoundError,
)

router = APIRouter(prefix="/api/workspaces", tags=["notes"])


def _to_note_response(note: Note) -> NoteResponse:
    return NoteResponse(
        note_id=note.note_id,
        anchor=PassageResponse(
            first_block_id=note.anchor.first_block_id,
            first_block_offset=note.anchor.first_block_offset,
            last_block_id=note.anchor.last_block_id,
            last_block_offset=note.anchor.last_block_offset,
            text=note.anchor.text,
        ),
        text=note.text,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _blocks_for(store, workspace_id: str) -> list[Block]:
    try:
        return store.get_document(workspace_id).blocks
    except DocumentNotFoundError:
        return []


@router.get("/{workspace_id}/notes", response_model=list[NoteResponse])
def list_notes(workspace_id: str, request: Request) -> list[NoteResponse]:
    store = request.app.state.store
    try:
        notes = store.list_notes(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()
    return [_to_note_response(n) for n in notes]


@router.post("/{workspace_id}/notes", status_code=201, response_model=NoteResponse)
def create_note(workspace_id: str, body: NoteCreateRequest, request: Request) -> NoteResponse:
    store = request.app.state.store
    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()

    anchor = Passage(
        first_block_id=body.anchor.first_block_id,
        first_block_offset=body.anchor.first_block_offset,
        last_block_id=body.anchor.last_block_id,
        last_block_offset=body.anchor.last_block_offset,
        text=body.anchor.text,
    )
    try:
        validate_passage(anchor, _blocks_for(store, workspace_id))
    except PassageValidationError as exc:
        raise bad_request_error(str(exc))

    now = datetime.now(timezone.utc)
    note = Note(
        note_id=generate_note_id(), anchor=anchor, text=body.text, created_at=now, updated_at=now
    )
    store.create_note(workspace_id, note)
    return _to_note_response(note)


@router.put("/{workspace_id}/notes/{note_id}", response_model=NoteResponse)
def update_note(
    workspace_id: str, note_id: str, body: NoteUpdateRequest, request: Request
) -> NoteResponse:
    store = request.app.state.store
    try:
        note = store.update_note(
            workspace_id, note_id, text=body.text, updated_at=datetime.now(timezone.utc)
        )
    except (WorkspaceNotFoundError, NoteNotFoundError):
        raise not_found_error()
    return _to_note_response(note)


@router.delete("/{workspace_id}/notes/{note_id}", status_code=204)
def delete_note(workspace_id: str, note_id: str, request: Request) -> None:
    store = request.app.state.store
    try:
        store.get_note(workspace_id, note_id)
    except (WorkspaceNotFoundError, NoteNotFoundError):
        raise not_found_error()
    store.delete_note(workspace_id, note_id)

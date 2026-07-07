from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.errors import (
    conflict_error,
    llm_unavailable_error,
    not_found_error,
    rate_limited_error,
)
from app.llm_client import LlmUnavailableError
from app.llm_prompts import build_journal_prompt, truncate_journal_inputs
from app.models import JournalResponse
from app.parsing import Block
from app.store import (
    DocumentNotFoundError,
    Journal,
    JournalNotFoundError,
    WorkspaceNotFoundError,
)
from app.untrusted import strip_untrusted_markup
from app.viewport import resolve_viewport_text

router = APIRouter(prefix="/api/workspaces", tags=["journal"])


def _to_response(journal: Journal) -> JournalResponse:
    return JournalResponse(text=journal.text, generated_at=journal.generated_at)


def _blocks_for(store, workspace_id: str) -> list[Block]:
    try:
        return store.get_document(workspace_id).blocks
    except DocumentNotFoundError:
        return []


@router.get("/{workspace_id}/journal", response_model=JournalResponse)
def get_journal(workspace_id: str, request: Request) -> JournalResponse:
    store = request.app.state.store
    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()
    try:
        journal = store.get_journal(workspace_id)
    except JournalNotFoundError:
        raise not_found_error()
    return _to_response(journal)


@router.post("/{workspace_id}/journal", response_model=JournalResponse)
def generate_journal(workspace_id: str, request: Request) -> JournalResponse:
    store = request.app.state.store
    limiter = request.app.state.journal_generation_limiter
    if not limiter.allow(workspace_id):
        raise rate_limited_error(limiter.retry_after(workspace_id))

    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()

    notes = store.list_notes(workspace_id)
    all_turns = store.list_all_turns(workspace_id)
    if not notes and not all_turns:
        raise conflict_error("Nothing to synthesize.")

    blocks = _blocks_for(store, workspace_id)
    turns = [
        (turn, resolve_viewport_text(blocks, turn.viewport.first_block_id, turn.viewport.last_block_id))
        for turn in all_turns
    ]

    previous_journal = store.get_journal(workspace_id).text if store.has_journal(workspace_id) else None

    if store.has_document(workspace_id):
        document = store.get_document(workspace_id)
        document_metadata = {"filename": document.filename, "block_count": len(document.blocks)}
    else:
        document_metadata = {}

    notes, turns = truncate_journal_inputs(notes, turns)
    prompt = build_journal_prompt(notes, turns, previous_journal, document_metadata)

    llm_client = request.app.state.llm_client
    try:
        journal_text = llm_client.generate_journal(prompt)
    except LlmUnavailableError:
        raise llm_unavailable_error(
            "Journal generation is currently unavailable; the previous journal, if any, is unchanged. Retry."
        )

    journal = Journal(text=strip_untrusted_markup(journal_text), generated_at=datetime.now(timezone.utc))
    store.put_journal(workspace_id, journal)
    return _to_response(journal)

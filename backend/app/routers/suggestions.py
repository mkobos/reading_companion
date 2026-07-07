from fastapi import APIRouter, Request

from app.errors import (
    bad_request_error,
    conflict_error,
    llm_unavailable_error,
    not_found_error,
    rate_limited_error,
)
from app.llm_client import LlmUnavailableError
from app.llm_prompts import build_suggestions_prompt
from app.models import SuggestionsRequest, SuggestionsResponse
from app.passages import Passage, PassageValidationError, validate_passage
from app.store import DocumentNotFoundError, WorkspaceNotFoundError
from app.untrusted import strip_untrusted_markup
from app.viewport import ViewportValidationError, resolve_viewport_text

router = APIRouter(prefix="/api/workspaces", tags=["suggestions"])


@router.post("/{workspace_id}/suggestions", response_model=SuggestionsResponse)
def create_suggestions(
    workspace_id: str, body: SuggestionsRequest, request: Request
) -> SuggestionsResponse:
    store = request.app.state.store
    limiter = request.app.state.suggestions_limiter
    if not limiter.allow(workspace_id):
        raise rate_limited_error(limiter.retry_after(workspace_id))

    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()
    if not store.has_document(workspace_id):
        raise conflict_error("Workspace has no document yet.")

    try:
        blocks = store.get_document(workspace_id).blocks
    except DocumentNotFoundError:
        blocks = []

    try:
        viewport_text = resolve_viewport_text(
            blocks, body.viewport.first_block_id, body.viewport.last_block_id
        )
    except ViewportValidationError as exc:
        raise bad_request_error(str(exc))

    anchor = Passage(
        first_block_id=body.anchor.first_block_id,
        first_block_offset=body.anchor.first_block_offset,
        last_block_id=body.anchor.last_block_id,
        last_block_offset=body.anchor.last_block_offset,
        text=body.anchor.text,
    )
    try:
        validate_passage(anchor, blocks)
    except PassageValidationError as exc:
        raise bad_request_error(str(exc))

    prompt = build_suggestions_prompt(viewport_text, anchor.text)
    llm_client = request.app.state.llm_client
    try:
        suggestions = llm_client.generate_suggestions(prompt)
    except LlmUnavailableError:
        raise llm_unavailable_error("Suggestions are currently unavailable. Retry.")

    return SuggestionsResponse(suggestions=[strip_untrusted_markup(s) for s in suggestions])

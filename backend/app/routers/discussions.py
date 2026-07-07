from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.discussion_agent_client import AgentInvocationError
from app.errors import (
    agent_failure_error,
    bad_request_error,
    conflict_error,
    not_found_error,
    rate_limited_error,
)
from app.ids import generate_discussion_id, generate_turn_id
from app.models import (
    DiscussionCreateRequest,
    DiscussionResponse,
    DiscussionSummaryResponse,
    PassageResponse,
    ToolCallResponse,
    TurnCreateRequest,
    TurnResponse,
    ViewportResponse,
)
from app.parsing import Block
from app.passages import Passage, PassageValidationError, validate_passage
from app.store import (
    Discussion,
    DiscussionNotFoundError,
    DocumentNotFoundError,
    Note,
    ToolCall,
    Turn,
    WorkspaceNotFoundError,
)
from app.viewport import Viewport, ViewportValidationError, resolve_viewport_text

router = APIRouter(prefix="/api/workspaces", tags=["discussions"])

_MAX_NOTES = 10
_MAX_HISTORY_TURNS = 2


def _to_viewport_response(viewport: Viewport) -> ViewportResponse:
    return ViewportResponse(
        first_block_id=viewport.first_block_id, last_block_id=viewport.last_block_id
    )


def _to_turn_response(turn: Turn) -> TurnResponse:
    return TurnResponse(
        turn_id=turn.turn_id,
        user_message=turn.user_message,
        agent_response=turn.agent_response,
        viewport=_to_viewport_response(turn.viewport),
        created_at=turn.created_at,
        tool_calls=[
            ToolCallResponse(tool=tc.tool, input_summary=tc.input_summary, result_summary=tc.result_summary)
            for tc in turn.tool_calls
        ],
    )


def _to_passage_response(anchor: Passage | None) -> PassageResponse | None:
    if anchor is None:
        return None
    return PassageResponse(
        first_block_id=anchor.first_block_id,
        first_block_offset=anchor.first_block_offset,
        last_block_id=anchor.last_block_id,
        last_block_offset=anchor.last_block_offset,
        text=anchor.text,
    )


def _to_discussion_response(discussion: Discussion, turns: list[Turn]) -> DiscussionResponse:
    return DiscussionResponse(
        discussion_id=discussion.discussion_id,
        anchor=_to_passage_response(discussion.anchor),
        created_at=discussion.created_at,
        turns=[_to_turn_response(t) for t in turns],
    )


def _to_summary_response(discussion: Discussion) -> DiscussionSummaryResponse:
    return DiscussionSummaryResponse(
        discussion_id=discussion.discussion_id,
        anchor=_to_passage_response(discussion.anchor),
        created_at=discussion.created_at,
        turn_count=discussion.turn_count,
        first_message_preview=discussion.first_message_preview,
    )


def _blocks_for(store, workspace_id: str) -> list[Block]:
    try:
        return store.get_document(workspace_id).blocks
    except DocumentNotFoundError:
        return []


def _notes_context(notes: list[Note], reference_block_id: str) -> list[dict]:
    def proximity(note: Note) -> int:
        return abs(int(note.anchor.first_block_id) - int(reference_block_id))

    nearest = sorted(notes, key=proximity)[:_MAX_NOTES]
    return [
        {
            "text": note.text,
            "passage_text": note.anchor.text,
            "created_at": note.created_at.isoformat(),
        }
        for note in nearest
    ]


def _history_context(turns: list[Turn], blocks: list[Block]) -> list[dict]:
    # The document's blocks are immutable once uploaded, so a past turn's
    # recorded viewport (block-ID range) always re-resolves to the same
    # text it had at the time — no need to persist the resolved text too.
    return [
        {
            "user_message": t.user_message,
            "agent_response": t.agent_response,
            "viewport_text": resolve_viewport_text(
                blocks, t.viewport.first_block_id, t.viewport.last_block_id
            ),
        }
        for t in turns
    ]


def _build_context(
    store,
    workspace_id: str,
    blocks: list[Block],
    viewport_text: str,
    passage_text: str | None,
    reference_block_id: str,
    exclude_discussion_id: str,
) -> dict:
    document = store.get_document(workspace_id)
    context: dict = {
        "viewport_text": viewport_text,
        "document_metadata": {"filename": document.filename, "block_count": len(blocks)},
        "document_blocks": [{"block_id": b.block_id, "text": b.text} for b in blocks],
    }
    if passage_text is not None:
        context["passage_text"] = passage_text

    notes = _notes_context(store.list_notes(workspace_id), reference_block_id)
    if notes:
        context["notes"] = notes

    history = store.list_recent_turns(
        workspace_id, exclude_discussion_id=exclude_discussion_id, limit=_MAX_HISTORY_TURNS
    )
    if history:
        context["discussion_history"] = _history_context(list(reversed(history)), blocks)

    if store.has_journal(workspace_id):
        context["journal"] = store.get_journal(workspace_id).text

    return context


@router.get("/{workspace_id}/discussions", response_model=list[DiscussionSummaryResponse])
def list_discussions(workspace_id: str, request: Request) -> list[DiscussionSummaryResponse]:
    store = request.app.state.store
    try:
        discussions = store.list_discussions(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()
    return [_to_summary_response(d) for d in discussions]


@router.post("/{workspace_id}/discussions", status_code=201, response_model=DiscussionResponse)
def create_discussion(
    workspace_id: str, body: DiscussionCreateRequest, request: Request
) -> DiscussionResponse:
    store = request.app.state.store
    limiter = request.app.state.discussion_creation_limiter
    if not limiter.allow(workspace_id):
        raise rate_limited_error(limiter.retry_after(workspace_id))

    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()
    if not store.has_document(workspace_id):
        raise conflict_error("Workspace has no document yet.")

    blocks = _blocks_for(store, workspace_id)
    try:
        viewport_text = resolve_viewport_text(
            blocks, body.viewport.first_block_id, body.viewport.last_block_id
        )
    except ViewportValidationError as exc:
        raise bad_request_error(str(exc))

    anchor: Passage | None = None
    passage_text: str | None = None
    if body.anchor is not None:
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
        passage_text = anchor.text

    reference_block_id = anchor.first_block_id if anchor is not None else body.viewport.first_block_id
    discussion_id = generate_discussion_id()
    context = _build_context(
        store,
        workspace_id,
        blocks,
        viewport_text,
        passage_text,
        reference_block_id,
        exclude_discussion_id=discussion_id,
    )

    session_id = f"{workspace_id}:{discussion_id}"
    agent_client = request.app.state.discussion_agent_client
    try:
        agent_client.create_session(session_id=session_id, user_id=workspace_id)
        result = agent_client.run_turn(
            session_id=session_id,
            user_id=workspace_id,
            user_message=body.message,
            context=context,
        )
    except AgentInvocationError:
        raise agent_failure_error()

    now = datetime.now(timezone.utc)
    first_turn = Turn(
        turn_id=generate_turn_id(),
        user_message=body.message,
        agent_response=result.response_text,
        viewport=Viewport(
            first_block_id=body.viewport.first_block_id, last_block_id=body.viewport.last_block_id
        ),
        created_at=now,
        tool_calls=[
            ToolCall(tool=tc.tool, input_summary=tc.input_summary, result_summary=tc.result_summary)
            for tc in result.tool_calls
        ],
    )
    discussion = Discussion(
        discussion_id=discussion_id,
        created_at=now,
        turn_count=1,
        first_message_preview=body.message,
        anchor=anchor,
    )
    store.create_discussion(workspace_id, discussion, first_turn)
    return _to_discussion_response(discussion, [first_turn])


@router.get(
    "/{workspace_id}/discussions/{discussion_id}", response_model=DiscussionResponse
)
def get_discussion(workspace_id: str, discussion_id: str, request: Request) -> DiscussionResponse:
    store = request.app.state.store
    try:
        discussion, turns = store.get_discussion(workspace_id, discussion_id)
    except (WorkspaceNotFoundError, DiscussionNotFoundError):
        raise not_found_error()
    return _to_discussion_response(discussion, turns)


@router.post(
    "/{workspace_id}/discussions/{discussion_id}/turns",
    status_code=201,
    response_model=TurnResponse,
)
def create_turn(
    workspace_id: str, discussion_id: str, body: TurnCreateRequest, request: Request
) -> TurnResponse:
    store = request.app.state.store
    limiter = request.app.state.discussion_turn_limiter
    if not limiter.allow(workspace_id):
        raise rate_limited_error(limiter.retry_after(workspace_id))

    try:
        discussion, _existing_turns = store.get_discussion(workspace_id, discussion_id)
    except (WorkspaceNotFoundError, DiscussionNotFoundError):
        raise not_found_error()

    blocks = _blocks_for(store, workspace_id)
    try:
        viewport_text = resolve_viewport_text(
            blocks, body.viewport.first_block_id, body.viewport.last_block_id
        )
    except ViewportValidationError as exc:
        raise bad_request_error(str(exc))

    passage_text = discussion.anchor.text if discussion.anchor is not None else None
    reference_block_id = (
        discussion.anchor.first_block_id if discussion.anchor is not None else body.viewport.first_block_id
    )
    context = _build_context(
        store,
        workspace_id,
        blocks,
        viewport_text,
        passage_text,
        reference_block_id,
        exclude_discussion_id=discussion_id,
    )

    session_id = f"{workspace_id}:{discussion_id}"
    agent_client = request.app.state.discussion_agent_client
    try:
        result = agent_client.run_turn(
            session_id=session_id,
            user_id=workspace_id,
            user_message=body.message,
            context=context,
        )
    except AgentInvocationError:
        raise agent_failure_error()

    turn = Turn(
        turn_id=generate_turn_id(),
        user_message=body.message,
        agent_response=result.response_text,
        viewport=Viewport(
            first_block_id=body.viewport.first_block_id, last_block_id=body.viewport.last_block_id
        ),
        created_at=datetime.now(timezone.utc),
        tool_calls=[
            ToolCall(tool=tc.tool, input_summary=tc.input_summary, result_summary=tc.result_summary)
            for tc in result.tool_calls
        ],
    )
    store.append_turn(workspace_id, discussion_id, turn)
    return _to_turn_response(turn)

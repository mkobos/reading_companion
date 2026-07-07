from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.blob import raw_document_key
from app.errors import not_found_error, rate_limited_error
from app.ids import generate_workspace_id
from app.models import WorkspaceDetailResponse, WorkspaceResponse
from app.store import Workspace, WorkspaceNotFoundError

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("", status_code=201, response_model=WorkspaceResponse)
def create_workspace(request: Request) -> WorkspaceResponse:
    limiter = request.app.state.workspace_creation_limiter
    client_key = _client_key(request)
    if not limiter.allow(client_key):
        raise rate_limited_error(limiter.retry_after(client_key))

    workspace = Workspace(
        workspace_id=generate_workspace_id(), created_at=datetime.now(timezone.utc)
    )
    request.app.state.store.create_workspace(workspace)
    return WorkspaceResponse(
        workspace_id=workspace.workspace_id,
        created_at=workspace.created_at,
        last_accessed_at=workspace.last_accessed_at,
    )


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace(workspace_id: str, request: Request) -> WorkspaceDetailResponse:
    store = request.app.state.store
    try:
        workspace = store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()

    return WorkspaceDetailResponse(
        workspace_id=workspace.workspace_id,
        created_at=workspace.created_at,
        last_accessed_at=workspace.last_accessed_at,
        has_document=store.has_document(workspace_id),
        note_count=len(store.list_notes(workspace_id)),
        discussion_count=store.count_discussions(workspace_id),
        # TODO: replace with a real check once the journal phase exists —
        # False is correct today, not a stub.
        has_journal=False,
    )


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: str, request: Request) -> None:
    store = request.app.state.store
    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()

    store.delete_workspace(workspace_id)
    request.app.state.blob_store.delete(raw_document_key(workspace_id))

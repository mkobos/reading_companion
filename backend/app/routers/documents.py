import os
from datetime import datetime, timezone

from fastapi import APIRouter, File, Request, UploadFile

from app.blob import raw_document_key
from app.errors import (
    bad_request_error,
    conflict_error,
    not_found_error,
    rate_limited_error,
)
from app.models import BlockResponse, DocumentViewResponse
from app.parsing import parse_markdown, parse_plain_text
from app.store import (
    Document,
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    WorkspaceNotFoundError,
)

router = APIRouter(prefix="/api/workspaces", tags=["documents"])

_EXTENSION_FORMATS = {".txt": "text", ".md": "markdown"}


def _detect_format(filename: str) -> str | None:
    _, ext = os.path.splitext(filename.lower())
    return _EXTENSION_FORMATS.get(ext)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _to_document_view(document: Document) -> DocumentViewResponse:
    return DocumentViewResponse(
        filename=document.filename,
        format=document.format,
        size_bytes=document.size_bytes,
        uploaded_at=document.uploaded_at,
        blocks=[
            BlockResponse(block_id=b.block_id, type=b.type, text=b.text, level=b.level)
            for b in document.blocks
        ],
    )


@router.post(
    "/{workspace_id}/document", status_code=201, response_model=DocumentViewResponse
)
async def upload_document(
    workspace_id: str, request: Request, file: UploadFile = File(...)
) -> DocumentViewResponse:
    store = request.app.state.store
    blob_store = request.app.state.blob_store
    settings = request.app.state.settings

    client_key = _client_key(request)
    ip_limiter = request.app.state.document_upload_ip_limiter
    if not ip_limiter.allow(client_key):
        raise rate_limited_error(ip_limiter.retry_after(client_key))
    workspace_limiter = request.app.state.document_upload_workspace_limiter
    if not workspace_limiter.allow(workspace_id):
        raise rate_limited_error(workspace_limiter.retry_after(workspace_id))

    try:
        store.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise not_found_error()

    if store.has_document(workspace_id):
        raise conflict_error(
            "Workspace already has a document; create a new workspace to upload another."
        )

    filename = file.filename or ""
    fmt = _detect_format(filename)
    if fmt is None:
        raise bad_request_error(
            "Unsupported file type. Only plain text (.txt) and Markdown (.md) files are accepted."
        )

    # Reject on Content-Length before touching the body when possible; the
    # capped .read() below is the backstop for chunked/lying requests (see
    # plan's Security Boundaries note on this endpoint's known limits).
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > settings.max_upload_size_bytes:
                raise bad_request_error(
                    f"File exceeds the maximum size of {settings.max_upload_size_bytes} bytes."
                )
        except ValueError:
            pass

    raw_bytes = await file.read(settings.max_upload_size_bytes + 1)
    if len(raw_bytes) > settings.max_upload_size_bytes:
        raise bad_request_error(
            f"File exceeds the maximum size of {settings.max_upload_size_bytes} bytes."
        )

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise bad_request_error("File is not valid UTF-8 text.")

    blocks = parse_markdown(text) if fmt == "markdown" else parse_plain_text(text)

    document = Document(
        filename=filename,
        format=fmt,
        size_bytes=len(raw_bytes),
        uploaded_at=datetime.now(timezone.utc),
        blocks=blocks,
    )
    try:
        store.put_document(workspace_id, document)
    except DocumentAlreadyExistsError:
        raise conflict_error(
            "Workspace already has a document; create a new workspace to upload another."
        )

    # Written after the store commit succeeds, so a losing race on
    # immutability never overwrites the original raw blob (see plan notes).
    blob_store.put(raw_document_key(workspace_id), raw_bytes)

    return _to_document_view(document)


@router.get("/{workspace_id}/document", response_model=DocumentViewResponse)
def get_document(workspace_id: str, request: Request) -> DocumentViewResponse:
    store = request.app.state.store
    try:
        document = store.get_document(workspace_id)
    except (WorkspaceNotFoundError, DocumentNotFoundError):
        raise not_found_error()
    return _to_document_view(document)

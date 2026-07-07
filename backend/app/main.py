from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.blob import BlobStore
from app.blob.gcs_blob_store import GcsBlobStore
from app.blob.memory_blob_store import InMemoryBlobStore
from app.config import Settings, load_settings
from app.discussion_agent_client import DiscussionAgentClient
from app.llm_client import LazyGenaiClient, LlmClient
from app.rate_limit import SlidingWindowRateLimiter
from app.routers import discussions, documents, journal, notes, suggestions, workspaces
from app.store import WorkspaceStore
from app.store.firestore_store import FirestoreStore
from app.store.memory_store import InMemoryWorkspaceStore


def create_app(
    settings: Settings | None = None,
    store: WorkspaceStore | None = None,
    blob_store: BlobStore | None = None,
    discussion_agent_client: DiscussionAgentClient | None = None,
    llm_client: LlmClient | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    store = store or (FirestoreStore() if _use_firestore() else InMemoryWorkspaceStore())
    blob_store = blob_store or (
        GcsBlobStore(settings.gcs_bucket_name)
        if settings.gcs_bucket_name
        else InMemoryBlobStore()
    )
    discussion_agent_client = discussion_agent_client or DiscussionAgentClient(
        base_url=settings.discussion_agent_url,
        timeout_seconds=settings.discussion_agent_timeout_seconds,
    )
    llm_client = llm_client or LlmClient(
        genai_client=LazyGenaiClient(settings.llm_timeout_seconds),
        suggestions_model=settings.suggestions_model,
        journal_model=settings.journal_model,
    )

    app = FastAPI(title="Reading Companion Backend")

    app.state.settings = settings
    app.state.store = store
    app.state.blob_store = blob_store
    app.state.discussion_agent_client = discussion_agent_client
    app.state.llm_client = llm_client
    app.state.workspace_creation_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.document_upload_ip_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.document_upload_workspace_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.discussion_creation_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.discussion_turn_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.suggestions_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.journal_generation_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    if settings.allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allow_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
        content = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request, _exc: RequestValidationError
    ) -> JSONResponse:
        # api.openapi.yaml documents 400 (the Error schema) for request
        # validation failures; FastAPI's default for these is 422.
        return JSONResponse(status_code=400, content={"message": "Invalid request."})

    app.include_router(workspaces.router)
    app.include_router(documents.router)
    app.include_router(notes.router)
    app.include_router(discussions.router)
    app.include_router(suggestions.router)
    app.include_router(journal.router)

    return app


def _use_firestore() -> bool:
    import os

    return bool(os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("FIRESTORE_EMULATOR_HOST"))


app = create_app()

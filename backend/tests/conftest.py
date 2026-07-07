import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.blob.memory_blob_store import InMemoryBlobStore
from app.config import Settings
from app.main import create_app
from app.store.memory_store import InMemoryWorkspaceStore

load_dotenv()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        max_upload_size_bytes=1024,
        rate_limit_max_requests=1000,
        rate_limit_window_seconds=60,
        gcs_bucket_name=None,
        allow_origins=[],
    )


@pytest.fixture
def store() -> InMemoryWorkspaceStore:
    return InMemoryWorkspaceStore()


@pytest.fixture
def blob_store() -> InMemoryBlobStore:
    return InMemoryBlobStore()


@pytest.fixture
def client(settings, store, blob_store) -> TestClient:
    app = create_app(settings=settings, store=store, blob_store=blob_store)
    return TestClient(app)

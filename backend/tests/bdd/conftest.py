"""pytest-bdd bindings for backend-observable scenarios in
spec/features/workspace-lifecycle.feature, document-upload.feature, and the
workspace-isolation scenarios in security.feature.

Only scenarios whose Given/When/Then are entirely API-observable are bound
here (named @scenario, not blanket scenarios(path), matching
discussion-agent's convention). Scenarios about cookies, redirects, or
client-side routing are frontend concerns and are deliberately not bound —
there is no frontend yet.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.blob.memory_blob_store import InMemoryBlobStore
from app.config import Settings
from app.main import create_app
from app.store.memory_store import InMemoryWorkspaceStore
from tests.conftest import FakeDiscussionAgentClient

FEATURES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "spec", "features")
)


@pytest.fixture
def bdd_state() -> dict:
    return {}


@pytest.fixture
def bdd_discussion_agent_client() -> FakeDiscussionAgentClient:
    return FakeDiscussionAgentClient()


@pytest.fixture
def bdd_client(bdd_discussion_agent_client) -> TestClient:
    settings = Settings(
        max_upload_size_bytes=1024,
        rate_limit_max_requests=1000,
        rate_limit_window_seconds=60,
        gcs_bucket_name=None,
        allow_origins=[],
        discussion_agent_url="http://discussion-agent.invalid",
        discussion_agent_timeout_seconds=5,
    )
    app = create_app(
        settings=settings,
        store=InMemoryWorkspaceStore(),
        blob_store=InMemoryBlobStore(),
        discussion_agent_client=bdd_discussion_agent_client,
    )
    return TestClient(app)

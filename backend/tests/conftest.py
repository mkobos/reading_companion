import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.blob.memory_blob_store import InMemoryBlobStore
from app.config import Settings
from app.discussion_agent_client import AgentInvocationError, AgentTurnResult
from app.main import create_app
from app.store.memory_store import InMemoryWorkspaceStore

load_dotenv()


class FakeDiscussionAgentClient:
    """Test double for DiscussionAgentClient — no HTTP, scripted responses.

    Default behavior (a canned success) is safe for tests that don't care
    about discussion-agent invocation; tests that do (tests/api/
    test_discussions.py) mutate `next_result`/`raise_on_*` before acting.
    """

    def __init__(self) -> None:
        self.create_session_calls: list[tuple[str, str]] = []
        self.run_turn_calls: list[dict] = []
        self.next_result = AgentTurnResult(response_text="Default fake response.")
        self.raise_on_create_session = False
        self.raise_on_run_turn = False

    def create_session(self, *, session_id: str, user_id: str) -> None:
        self.create_session_calls.append((session_id, user_id))
        if self.raise_on_create_session:
            raise AgentInvocationError("fake create_session failure")

    def run_turn(self, *, session_id: str, user_id: str, user_message: str, context: dict) -> AgentTurnResult:
        self.run_turn_calls.append(
            {
                "session_id": session_id,
                "user_id": user_id,
                "user_message": user_message,
                "context": context,
            }
        )
        if self.raise_on_run_turn:
            raise AgentInvocationError("fake run_turn failure")
        return self.next_result


@pytest.fixture
def settings() -> Settings:
    return Settings(
        max_upload_size_bytes=1024,
        rate_limit_max_requests=1000,
        rate_limit_window_seconds=60,
        gcs_bucket_name=None,
        allow_origins=[],
        discussion_agent_url="http://discussion-agent.invalid",
        discussion_agent_timeout_seconds=5,
    )


@pytest.fixture
def store() -> InMemoryWorkspaceStore:
    return InMemoryWorkspaceStore()


@pytest.fixture
def blob_store() -> InMemoryBlobStore:
    return InMemoryBlobStore()


@pytest.fixture
def discussion_agent_client() -> FakeDiscussionAgentClient:
    return FakeDiscussionAgentClient()


@pytest.fixture
def client(settings, store, blob_store, discussion_agent_client) -> TestClient:
    app = create_app(
        settings=settings,
        store=store,
        blob_store=blob_store,
        discussion_agent_client=discussion_agent_client,
    )
    return TestClient(app)

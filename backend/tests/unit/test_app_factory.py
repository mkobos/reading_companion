from app.config import Settings
from app.discussion_agent_client import DiscussionAgentClient
from app.fake_discussion_agent_client import FakeDiscussionAgentClient
from app.fake_llm_client import FakeLlmClient
from app.llm_client import LlmClient
from app.main import create_app


def _settings() -> Settings:
    return Settings(
        max_upload_size_bytes=1024,
        rate_limit_max_requests=1000,
        rate_limit_window_seconds=60,
        gcs_bucket_name=None,
        allow_origins=[],
        discussion_agent_url="http://discussion-agent.invalid",
        discussion_agent_timeout_seconds=5,
        suggestions_model="fake-suggestions-model",
        journal_model="fake-journal-model",
        llm_timeout_seconds=5,
    )


def test_discussion_agent_fake_env_var_wires_fake_client(monkeypatch) -> None:
    monkeypatch.setenv("DISCUSSION_AGENT_FAKE", "1")

    app = create_app(settings=_settings())

    assert isinstance(app.state.discussion_agent_client, FakeDiscussionAgentClient)


def test_discussion_agent_fake_env_var_unset_wires_real_client(monkeypatch) -> None:
    monkeypatch.delenv("DISCUSSION_AGENT_FAKE", raising=False)

    app = create_app(settings=_settings())

    assert isinstance(app.state.discussion_agent_client, DiscussionAgentClient)


def test_llm_fake_env_var_wires_fake_client(monkeypatch) -> None:
    monkeypatch.setenv("LLM_FAKE", "1")

    app = create_app(settings=_settings())

    assert isinstance(app.state.llm_client, FakeLlmClient)


def test_llm_fake_env_var_unset_wires_real_client(monkeypatch) -> None:
    monkeypatch.delenv("LLM_FAKE", raising=False)

    app = create_app(settings=_settings())

    assert isinstance(app.state.llm_client, LlmClient)

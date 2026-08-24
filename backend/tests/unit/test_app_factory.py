from app.config import Settings
from app.discussion_agent_client import DiscussionAgentClient
from app.fake_discussion_agent_client import FakeDiscussionAgentClient
from app.fake_llm_client import FakeLlmClient
from app.llm_client import LlmClient
from app.main import create_app
from app.ollama_llm_client import OllamaLlmClient


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


def test_llm_backend_fake_wires_fake_client(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")

    app = create_app(settings=_settings())

    assert isinstance(app.state.llm_client, FakeLlmClient)


def test_llm_backend_unset_wires_real_client(monkeypatch) -> None:
    monkeypatch.delenv("LLM_BACKEND", raising=False)

    app = create_app(settings=_settings())

    assert isinstance(app.state.llm_client, LlmClient)


def test_llm_backend_ollama_wires_ollama_client(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")

    app = create_app(settings=_settings())

    assert isinstance(app.state.llm_client, OllamaLlmClient)


def test_llm_backend_and_discussion_agent_axes_are_independent(monkeypatch) -> None:
    """LLM_BACKEND=fake must not force DISCUSSION_AGENT_FAKE on — a
    developer can want fake suggestions/journal while still exercising a
    real (possibly Ollama-backed) discussion-agent process."""
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.delenv("DISCUSSION_AGENT_FAKE", raising=False)

    app = create_app(settings=_settings())

    assert isinstance(app.state.llm_client, FakeLlmClient)
    assert isinstance(app.state.discussion_agent_client, DiscussionAgentClient)

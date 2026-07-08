import pytest

from app.fake_llm_client import FORCE_ERROR_ENV_VAR, FakeLlmClient
from app.llm_client import LlmUnavailableError


def test_generate_suggestions_returns_deterministic_list_of_3_to_5() -> None:
    client = FakeLlmClient()

    suggestions = client.generate_suggestions("some prompt")

    assert 3 <= len(suggestions) <= 5
    assert all(isinstance(s, str) and s for s in suggestions)
    # Deterministic: calling again yields the same result.
    assert client.generate_suggestions("some prompt") == suggestions


def test_generate_journal_returns_deterministic_markdown_string() -> None:
    client = FakeLlmClient()

    journal_text = client.generate_journal("some prompt")

    assert isinstance(journal_text, str)
    assert journal_text
    assert client.generate_journal("some prompt") == journal_text


def test_generate_suggestions_raises_when_forced_error_env_var_set(monkeypatch) -> None:
    monkeypatch.setenv(FORCE_ERROR_ENV_VAR, "1")
    client = FakeLlmClient()

    with pytest.raises(LlmUnavailableError):
        client.generate_suggestions("some prompt")


def test_generate_journal_raises_when_forced_error_env_var_set(monkeypatch) -> None:
    monkeypatch.setenv(FORCE_ERROR_ENV_VAR, "1")
    client = FakeLlmClient()

    with pytest.raises(LlmUnavailableError):
        client.generate_journal("some prompt")


def test_generate_suggestions_succeeds_when_forced_error_env_var_unset(monkeypatch) -> None:
    monkeypatch.delenv(FORCE_ERROR_ENV_VAR, raising=False)
    client = FakeLlmClient()

    assert client.generate_suggestions("some prompt")

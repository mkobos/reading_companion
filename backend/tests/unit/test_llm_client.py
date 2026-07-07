"""Unit tests for app.llm_client.LlmClient, using a fake genai-client-shaped
double (no real network call — mirrors DiscussionAgentClient's transport
injection pattern in tests/unit/test_discussion_agent_client.py)."""

import pytest
from google.genai import errors

from app.llm_client import LlmClient, LlmUnavailableError


class _FakeResponse:
    def __init__(self, parsed):
        self.parsed = parsed


class _FakeModels:
    def __init__(self, parsed=None, exception=None):
        self._parsed = parsed
        self._exception = exception
        self.calls: list[dict] = []

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self._exception is not None:
            raise self._exception
        return _FakeResponse(self._parsed)


class _FakeGenaiClient:
    def __init__(self, models: _FakeModels):
        self.models = models


class _FakeSuggestionsOutput:
    def __init__(self, suggestions):
        self.suggestions = suggestions


class _FakeJournalOutput:
    def __init__(self, journal_markdown):
        self.journal_markdown = journal_markdown


def _client(models: _FakeModels) -> LlmClient:
    return LlmClient(
        genai_client=_FakeGenaiClient(models),
        suggestions_model="fake-suggestions-model",
        journal_model="fake-journal-model",
    )


def test_generate_suggestions_returns_the_parsed_list():
    models = _FakeModels(parsed=_FakeSuggestionsOutput(["Question one?", "Question two?"]))

    result = _client(models).generate_suggestions("some prompt")

    assert result == ["Question one?", "Question two?"]
    assert models.calls[0]["model"] == "fake-suggestions-model"
    assert models.calls[0]["contents"] == "some prompt"


def test_generate_journal_returns_the_parsed_markdown():
    models = _FakeModels(parsed=_FakeJournalOutput("# Journal\n\nSome synthesis."))

    result = _client(models).generate_journal("some prompt")

    assert result == "# Journal\n\nSome synthesis."
    assert models.calls[0]["model"] == "fake-journal-model"


def test_api_error_raises_llm_unavailable():
    models = _FakeModels(exception=errors.ServerError(503, {"error": {"message": "down"}}))

    with pytest.raises(LlmUnavailableError):
        _client(models).generate_suggestions("some prompt")


def test_no_parsed_output_raises_llm_unavailable():
    models = _FakeModels(parsed=None)

    with pytest.raises(LlmUnavailableError):
        _client(models).generate_journal("some prompt")

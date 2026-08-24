"""Unit tests for app.ollama_llm_client.OllamaLlmClient, using a fake
litellm-completion-shaped double (no real network call, no litellm import
— mirrors test_llm_client.py's transport injection pattern).
"""

import json

import openai
import pytest

from app.llm_client import LlmUnavailableError
from app.llm_contracts import _SUGGESTIONS_INSTRUCTION
from app.ollama_llm_client import OllamaLlmClient


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletion:
    def __init__(self, content=None, exception=None):
        self._content = content
        self._exception = exception
        self.calls: list[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self._exception is not None:
            raise self._exception
        return _FakeResponse(self._content)


def _client(completion: _FakeCompletion) -> OllamaLlmClient:
    return OllamaLlmClient(
        completion=completion,
        model="qwen3:8b",
        api_base="http://localhost:11434",
        timeout_seconds=15,
    )


def test_generate_suggestions_returns_the_parsed_list():
    completion = _FakeCompletion(content=json.dumps({"suggestions": ["Q1?", "Q2?"]}))

    result = _client(completion).generate_suggestions("some prompt")

    assert result == ["Q1?", "Q2?"]
    call = completion.calls[0]
    assert call["model"] == "ollama_chat/qwen3:8b"
    assert call["api_base"] == "http://localhost:11434"
    assert call["timeout"] == 15
    assert call["messages"] == [
        {"role": "system", "content": _SUGGESTIONS_INSTRUCTION},
        {"role": "user", "content": "some prompt"},
    ]
    assert call["response_format"].__name__ == "_SuggestionsOutput"


def test_generate_journal_returns_the_parsed_markdown():
    completion = _FakeCompletion(
        content=json.dumps({"journal_markdown": "# Journal\n\nSome synthesis."})
    )

    result = _client(completion).generate_journal("some prompt")

    assert result == "# Journal\n\nSome synthesis."
    assert completion.calls[0]["model"] == "ollama_chat/qwen3:8b"


def test_malformed_json_raises_llm_unavailable():
    completion = _FakeCompletion(content="not json")

    with pytest.raises(LlmUnavailableError):
        _client(completion).generate_suggestions("some prompt")


def test_valid_json_missing_required_field_raises_llm_unavailable():
    completion = _FakeCompletion(content=json.dumps({"unexpected": "shape"}))

    with pytest.raises(LlmUnavailableError):
        _client(completion).generate_suggestions("some prompt")


def test_completion_raising_openai_error_raises_llm_unavailable():
    completion = _FakeCompletion(exception=openai.APIConnectionError(request=None))

    with pytest.raises(LlmUnavailableError):
        _client(completion).generate_suggestions("some prompt")

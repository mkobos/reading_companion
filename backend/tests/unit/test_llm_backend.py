"""Unit tests for app.llm_backend's LLM_BACKEND resolution and guards.

Governs only backend's own suggestions/journal client — independent of
DISCUSSION_AGENT_FAKE/DISCUSSION_AGENT_URL, which choose the transport to
a separate discussion-agent process (see app/llm_backend.py's docstring).
"""

import pytest

from app.config import Settings
from app.fake_llm_client import FakeLlmClient
from app.llm_backend import resolve_llm_client
from app.llm_client import LlmClient
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


# --- resolution matrix ---


def test_unset_backend_resolves_to_llm_client(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)

    assert isinstance(resolve_llm_client(_settings()), LlmClient)


def test_vertex_backend_resolves_to_llm_client(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "vertex")

    assert isinstance(resolve_llm_client(_settings()), LlmClient)


def test_fake_backend_resolves_to_fake_llm_client(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "fake")

    assert isinstance(resolve_llm_client(_settings()), FakeLlmClient)


def test_ollama_backend_resolves_to_ollama_llm_client(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")

    client = resolve_llm_client(_settings())

    assert isinstance(client, OllamaLlmClient)
    assert client.model == "qwen3:8b"
    assert client.api_base == "http://localhost:11434"


# --- fail-loud contract ---


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "openai")

    with pytest.raises(ValueError):
        resolve_llm_client(_settings())


def test_ollama_backend_without_model_raises(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    with pytest.raises(ValueError):
        resolve_llm_client(_settings())


# --- security assertions (spec/threat_model.md) ---


@pytest.mark.parametrize("runtime_marker", ["K_SERVICE", "GOOGLE_CLOUD_AGENT_ENGINE_ID"])
@pytest.mark.parametrize("backend_setup", ["fake", "ollama"])
def test_non_vertex_backends_refuse_to_run_under_a_deployed_runtime_marker(
    monkeypatch, runtime_marker, backend_setup
):
    monkeypatch.setenv("LLM_BACKEND", backend_setup)
    if backend_setup == "ollama":
        monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setenv(runtime_marker, "some-deployed-value")

    with pytest.raises(ValueError):
        resolve_llm_client(_settings())


@pytest.mark.parametrize(
    "non_loopback_base",
    ["http://evil.example.com:11434", "http://192.168.1.50:11434"],
)
def test_ollama_backend_refuses_a_non_loopback_api_base(monkeypatch, non_loopback_base):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setenv("OLLAMA_API_BASE", non_loopback_base)

    with pytest.raises(ValueError):
        resolve_llm_client(_settings())


@pytest.mark.parametrize("backend_setup", ["fake", "ollama"])
def test_non_vertex_backends_require_no_gcp_credentials(monkeypatch, backend_setup):
    monkeypatch.setenv("LLM_BACKEND", backend_setup)
    if backend_setup == "ollama":
        monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    for credential_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(credential_var, raising=False)

    resolve_llm_client(_settings())

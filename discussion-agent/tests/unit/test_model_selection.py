"""Unit tests for app.model_selection's LLM_BACKEND switch.

Binds the local-dev-only alternatives: with LLM_BACKEND unset, model
construction must be byte-identical to today's Gemini/Vertex path (no
production behavior change); with LLM_BACKEND=ollama, it must build a
google.adk.models.lite_llm.LiteLlm targeting a local Ollama server;
with LLM_BACKEND=fake, it must build app.fake_model.FakeLlm.

Constructing LiteLlm makes no network call and does not import litellm
(that import is deferred to first use), so these tests need no Ollama
server, no network, and no credentials.
"""

import pytest
from google.adk.models import Gemini
from google.adk.models.lite_llm import LiteLlm

from app.fake_model import FakeLlm
from app.model_selection import build_agent_model, supports_search_grounding

# --- default / production path (LLM_BACKEND unset or "vertex") ---


def test_unset_backend_builds_gemini_pro_model():
    model = build_agent_model()

    assert isinstance(model, Gemini)
    assert model.model == "gemini-2.5-pro"


def test_unset_backend_preserves_retry_options():
    model = build_agent_model()

    assert model.retry_options is not None
    assert model.retry_options.attempts == 3


def test_vertex_backend_is_equivalent_to_unset(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "vertex")

    model = build_agent_model()

    assert isinstance(model, Gemini)
    assert model.model == "gemini-2.5-pro"


def test_unset_backend_supports_search_grounding():
    assert supports_search_grounding() is True


# --- opt-in local path (LLM_BACKEND=ollama) ---


def test_ollama_backend_builds_lite_llm_with_ollama_chat_model(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")

    model = build_agent_model()

    assert isinstance(model, LiteLlm)
    assert model.model == "ollama_chat/qwen3:8b"


def test_ollama_backend_forwards_api_base(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setenv("OLLAMA_API_BASE", "http://127.0.0.1:11434")

    model = build_agent_model()

    assert model._additional_args["api_base"] == "http://127.0.0.1:11434"


def test_ollama_backend_defaults_api_base_to_localhost(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")

    model = build_agent_model()

    assert model._additional_args["api_base"] == "http://localhost:11434"


def test_ollama_backend_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "OLLAMA")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")

    model = build_agent_model()

    assert isinstance(model, LiteLlm)


def test_ollama_backend_does_not_support_search_grounding(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")

    assert supports_search_grounding() is False


# --- opt-in fake path (LLM_BACKEND=fake) ---


def test_fake_backend_builds_fake_llm(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "fake")

    model = build_agent_model()

    assert isinstance(model, FakeLlm)


def test_fake_backend_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "FAKE")

    model = build_agent_model()

    assert isinstance(model, FakeLlm)


def test_fake_backend_does_not_support_search_grounding(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "fake")

    assert supports_search_grounding() is False


def test_fake_backend_requires_no_gcp_credentials(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "fake")
    for credential_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(credential_var, raising=False)

    model = build_agent_model()

    assert isinstance(model, FakeLlm)


# --- fail-loud contract ---


def test_ollama_backend_without_model_raises(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    with pytest.raises(ValueError):
        build_agent_model()


def test_unknown_backend_raises_rather_than_falling_back_to_gemini(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "openai")

    with pytest.raises(ValueError):
        build_agent_model()


# --- security assertions (spec/threat_model.md) ---


@pytest.mark.parametrize("runtime_marker", ["K_SERVICE", "GOOGLE_CLOUD_AGENT_ENGINE_ID"])
def test_ollama_backend_refuses_to_run_under_a_deployed_runtime_marker(
    monkeypatch, runtime_marker
):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setenv(runtime_marker, "some-deployed-value")

    with pytest.raises(ValueError):
        build_agent_model()


@pytest.mark.parametrize("runtime_marker", ["K_SERVICE", "GOOGLE_CLOUD_AGENT_ENGINE_ID"])
def test_fake_backend_refuses_to_run_under_a_deployed_runtime_marker(
    monkeypatch, runtime_marker
):
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.setenv(runtime_marker, "some-deployed-value")

    with pytest.raises(ValueError):
        build_agent_model()


@pytest.mark.parametrize(
    "non_loopback_base",
    ["http://evil.example.com:11434", "http://192.168.1.50:11434"],
)
def test_ollama_backend_refuses_a_non_loopback_api_base(monkeypatch, non_loopback_base):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setenv("OLLAMA_API_BASE", non_loopback_base)

    with pytest.raises(ValueError):
        build_agent_model()


def test_ollama_backend_requires_no_gcp_credentials(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    for credential_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(credential_var, raising=False)

    model = build_agent_model()

    assert isinstance(model, LiteLlm)

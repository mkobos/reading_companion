"""LLM backend selection (spec/technical_specification.md §8).

Local development can opt into a self-hosted Ollama model, or a canned
fake model, instead of Gemini via Vertex AI, via the LLM_BACKEND env var
(vertex | ollama | fake). This is a developer convenience only: Vertex AI
Agent Engine (the deployed target) cannot reach a developer's localhost
and has no use for canned responses, LLM_BACKEND is never set by Terraform
or `agents-cli deploy`, and eval scores are only meaningful on the default
Gemini/Vertex backend (see the Makefile's eval-gate guard).
"""

import os

from google.adk.models import Gemini
from google.genai import types

_DEPLOYED_RUNTIME_MARKERS = ("K_SERVICE", "GOOGLE_CLOUD_AGENT_ENGINE_ID")
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _backend() -> str:
    return os.environ.get("LLM_BACKEND", "vertex").strip().lower()


def supports_search_grounding() -> bool:
    """False for any backend other than vertex.

    web_search (app/web_search.py) relies on Gemini/Vertex search grounding,
    which cannot run behind Ollama or the fake model; both those backends
    must stub the tool instead.
    """
    return _backend() == "vertex"


def _refuse_if_deployed_runtime(backend: str) -> None:
    for marker in _DEPLOYED_RUNTIME_MARKERS:
        if os.environ.get(marker):
            raise ValueError(
                f"LLM_BACKEND={backend} is a local-development-only option "
                f"and cannot run under a deployed runtime (detected {marker})."
            )


def _ollama_api_base() -> str:
    api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
    host = api_base.split("://", 1)[-1].split(":", 1)[0].split("/", 1)[0]
    if host not in _LOOPBACK_HOSTS:
        raise ValueError(
            f"OLLAMA_API_BASE must be a loopback address (got {api_base!r}); "
            "the local LLM backend must never send workspace content off-machine."
        )
    return api_base


def build_agent_model():
    """Builds the discussion agent's model per LLM_BACKEND (default: vertex)."""
    backend = _backend()
    if backend == "vertex":
        return Gemini(
            # No "-latest" alias resolves for Pro tier on this project/region
            # today (confirmed via `client.models.list()` / a direct
            # generate_content call, unlike "gemini-flash-latest" which
            # does) — pinned to the current stable Pro release instead;
            # re-check at future implementation touch points per
            # spec/technical_specification.md §8.
            model="gemini-2.5-pro",
            retry_options=types.HttpRetryOptions(attempts=3),
        )
    if backend == "ollama":
        _refuse_if_deployed_runtime(backend)
        model = os.environ.get("OLLAMA_MODEL")
        if not model:
            raise ValueError(
                "LLM_BACKEND=ollama requires OLLAMA_MODEL to be set to a "
                "tool-calling-capable Ollama model (e.g. qwen3:8b)."
            )
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(model=f"ollama_chat/{model}", api_base=_ollama_api_base())
    if backend == "fake":
        _refuse_if_deployed_runtime(backend)
        from app.fake_model import FakeLlm

        return FakeLlm()
    raise ValueError(
        f"Unknown LLM_BACKEND {backend!r}; expected 'vertex', 'ollama', or 'fake'."
    )

"""LLM backend selection for backend's own suggestions/journal calls
(spec/technical_specification.md §8).

Governs only app.state.llm_client — i.e. what model backend/ itself calls
directly for suggestions/journal (app/llm_client.py's LlmClient,
app/ollama_llm_client.py's OllamaLlmClient, or app/fake_llm_client.py's
FakeLlmClient). It is deliberately independent of DISCUSSION_AGENT_URL /
DISCUSSION_AGENT_FAKE, which choose backend's *transport* to a separate
discussion-agent process — that process has its own LLM_BACKEND
(discussion-agent/app/model_selection.py). Two orthogonal axes: this
module answers "what model does backend itself call", not "how are
discussions served".

Mirrors discussion-agent/app/model_selection.py's guards (deployed-runtime
refusal, loopback-only OLLAMA_API_BASE) — duplicated rather than shared,
since backend/ and discussion-agent/ are separate deployables with no
common package. Keep both in sync by hand when editing either.
"""

import os

from app.llm_client import LazyGenaiClient, LlmClient, LlmClientLike

_DEPLOYED_RUNTIME_MARKERS = ("K_SERVICE", "GOOGLE_CLOUD_AGENT_ENGINE_ID")
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _backend() -> str:
    return os.environ.get("LLM_BACKEND", "vertex").strip().lower()


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


def resolve_llm_client(settings) -> LlmClientLike:
    """Builds backend's suggestions/journal client per LLM_BACKEND (default: vertex)."""
    backend = _backend()
    if backend == "vertex":
        return LlmClient(
            genai_client=LazyGenaiClient(settings.llm_timeout_seconds),
            suggestions_model=settings.suggestions_model,
            journal_model=settings.journal_model,
        )
    if backend == "fake":
        _refuse_if_deployed_runtime(backend)
        from app.fake_llm_client import FakeLlmClient

        return FakeLlmClient()
    if backend == "ollama":
        _refuse_if_deployed_runtime(backend)
        model = os.environ.get("OLLAMA_MODEL")
        if not model:
            raise ValueError(
                "LLM_BACKEND=ollama requires OLLAMA_MODEL to be set to an "
                "Ollama model that supports JSON-schema structured output "
                "(e.g. qwen3:8b)."
            )
        from litellm import completion

        from app.ollama_llm_client import OllamaLlmClient

        return OllamaLlmClient(
            completion=completion,
            model=model,
            api_base=_ollama_api_base(),
            timeout_seconds=settings.llm_timeout_seconds,
        )
    raise ValueError(
        f"Unknown LLM_BACKEND {backend!r}; expected 'vertex', 'ollama', or 'fake'."
    )

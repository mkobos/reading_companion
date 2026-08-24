"""Unit tests for web_search's behavior under a non-vertex LLM_BACKEND.

ADK's built-in google_search grounding tool requires Gemini/Vertex and
cannot run behind an Ollama model or the fake model at all. Under
LLM_BACKEND=ollama or LLM_BACKEND=fake, build_web_search_tool() must still
register a same-signature web_search tool (so the agent's tool inventory
is identical across backends — see spec/features/security.feature's
"Tools limit the blast radius"), but it must return a canned, wrapped
"unavailable" message instead of attempting any network call.
"""

import inspect

import pytest

from app.web_search import build_web_search_tool


def _set_non_vertex_backend(monkeypatch, backend):
    monkeypatch.setenv("LLM_BACKEND", backend)
    if backend == "ollama":
        monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["ollama", "fake"])
async def test_web_search_under_non_vertex_backend_returns_wrapped_unavailable_message(
    monkeypatch, backend
):
    _set_non_vertex_backend(monkeypatch, backend)

    web_search = build_web_search_tool()
    result = await web_search("What is the capital of France?")

    assert result.startswith('<untrusted source="tool_result">')
    assert result.endswith("</untrusted>")
    assert "unavailable" in result.lower()


@pytest.mark.parametrize("backend", ["ollama", "fake"])
def test_web_search_tool_signature_unchanged_under_non_vertex_backend(monkeypatch, backend):
    _set_non_vertex_backend(monkeypatch, backend)

    web_search = build_web_search_tool()

    assert list(inspect.signature(web_search).parameters) == ["query"]


def test_web_search_under_vertex_backend_builds_the_real_tool(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "vertex")

    web_search = build_web_search_tool()

    assert list(inspect.signature(web_search).parameters) == ["query"]

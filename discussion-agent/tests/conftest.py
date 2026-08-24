"""Loads `.env` before test collection.

`agents-cli eval generate`/`grade` and `app/fast_api_app.py` already call
`load_dotenv()` themselves, but plain `pytest` does not — without this, any
test that makes a real Vertex/AI-Studio call (see AGENTS.md's live-model
tests) fails with a misleading "No API key was provided" error instead of
picking up the project's real credentials.
"""

import pytest
from dotenv import load_dotenv

load_dotenv()

_LOCAL_BACKEND_VARS = (
    "LLM_BACKEND",
    "OLLAMA_MODEL",
    "OLLAMA_API_BASE",
)


@pytest.fixture(autouse=True)
def _default_llm_backend(monkeypatch):
    """Isolates tests from a developer's local LLM_BACKEND setting.

    load_dotenv() above pulls in the project's .env, so a developer running
    a non-default backend (see app.model_selection) would otherwise
    silently flip every agent-construction test onto that path — including
    ones asserting the production Gemini/tool structure. Tests that want a
    non-default backend opt in explicitly via monkeypatch.setenv.
    """
    for var in _LOCAL_BACKEND_VARS:
        monkeypatch.delenv(var, raising=False)

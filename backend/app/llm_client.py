"""Direct (non-agent) Gemini calls for suggestions and journal synthesis.

Wraps google.genai.Client for the two "plain LLM completion" entry points
from spec/contracts/agent-contract.yaml (suggestions_call, journal_call) —
tool-free, schema-constrained single-turn calls, unlike
discussion_agent_client.py's ADK-agent invocation. The genai client is
constructor-injected (mirroring DiscussionAgentClient's transport injection)
so tests exercise this module against a fake implementing the same
`.models.generate_content(...)` shape, with no real network calls.
"""

from dataclasses import dataclass
from typing import Protocol

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.llm_contracts import (
    _JOURNAL_INSTRUCTION,
    _SUGGESTIONS_INSTRUCTION,
    _JournalOutput,
    _SuggestionsOutput,
)


class LlmUnavailableError(Exception):
    """Raised on any failure to produce a usable completion: network error,
    API error, or a response with no parsed structured output. Callers must
    treat this per api.openapi.yaml's 503 responses: nothing persisted, and
    for journal generation, any previously stored journal is left
    untouched."""


class _Models(Protocol):
    def generate_content(self, *, model: str, contents: str, config: object) -> object: ...


class GenaiClientLike(Protocol):
    models: _Models


class LlmClientLike(Protocol):
    """The suggestions/journal call interface app.state.llm_client must
    satisfy — shared by LlmClient (Vertex), OllamaLlmClient (local Ollama),
    and FakeLlmClient (canned), so app/main.py can wire any of the three
    interchangeably."""

    def generate_suggestions(self, prompt: str) -> list[str]: ...

    def generate_journal(self, prompt: str) -> str: ...


class LazyGenaiClient:
    """Defers genai.Client() construction until the first actual call.

    genai.Client() validates credentials (Vertex ADC or GEMINI_API_KEY)
    eagerly at construction time and raises if none are configured. Since
    LlmClient is built once at app startup (app/main.py), an eager
    construction here would crash the whole app just from missing LLM
    credentials, even for requests that never touch suggestions/journal.
    """

    def __init__(self, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds
        self._client: genai.Client | None = None

    @property
    def models(self) -> _Models:
        if self._client is None:
            self._client = genai.Client(
                http_options=types.HttpOptions(timeout=int(self._timeout_seconds * 1000))
            )
        return self._client.models


@dataclass(frozen=True)
class LlmClient:
    genai_client: GenaiClientLike
    suggestions_model: str
    journal_model: str

    def generate_suggestions(self, prompt: str) -> list[str]:
        output = self._generate(
            self.suggestions_model, _SUGGESTIONS_INSTRUCTION, prompt, _SuggestionsOutput
        )
        return output.suggestions

    def generate_journal(self, prompt: str) -> str:
        output = self._generate(self.journal_model, _JOURNAL_INSTRUCTION, prompt, _JournalOutput)
        return output.journal_markdown

    def _generate(
        self, model: str, system_instruction: str, prompt: str, response_schema: type[BaseModel]
    ) -> BaseModel:
        try:
            response = self.genai_client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
        except (errors.APIError, httpx.HTTPError) as exc:
            raise LlmUnavailableError(f"LLM call failed: {exc}") from exc
        if response.parsed is None:
            raise LlmUnavailableError("LLM returned no usable structured output.")
        return response.parsed

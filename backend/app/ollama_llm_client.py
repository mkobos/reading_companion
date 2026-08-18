"""Local-dev-only Ollama-backed suggestions/journal calls.

Mirrors LlmClient's (app/llm_client.py) shape and exact prompts/schemas
(app/llm_contracts.py) but calls a local Ollama model via litellm's
`completion()` instead of google.genai. Ollama's ollama_chat provider
supports JSON-schema-constrained generation, so litellm's
`response_format=<PydanticModel>` reuses the same structured-output
contract the Vertex path already relies on — see app/llm_backend.py for
where this is wired in (LLM_BACKEND=ollama) and the loopback/deployed-
runtime guards.

`completion` is constructor-injected (mirroring LazyGenaiClient's
transport injection) so tests exercise this module with no litellm
import, no network, and no Ollama server.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.llm_client import LlmUnavailableError
from app.llm_contracts import (
    _JOURNAL_INSTRUCTION,
    _SUGGESTIONS_INSTRUCTION,
    _JournalOutput,
    _SuggestionsOutput,
)


@dataclass(frozen=True)
class OllamaLlmClient:
    completion: Callable
    model: str
    api_base: str
    timeout_seconds: float

    def generate_suggestions(self, prompt: str) -> list[str]:
        output = self._generate(_SUGGESTIONS_INSTRUCTION, prompt, _SuggestionsOutput)
        return output.suggestions

    def generate_journal(self, prompt: str) -> str:
        output = self._generate(_JOURNAL_INSTRUCTION, prompt, _JournalOutput)
        return output.journal_markdown

    def _generate(
        self, system_instruction: str, prompt: str, response_schema: type[BaseModel]
    ) -> BaseModel:
        import openai

        try:
            response = self.completion(
                model=f"ollama_chat/{self.model}",
                api_base=self.api_base,
                timeout=self.timeout_seconds,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                response_format=response_schema,
            )
            content = response.choices[0].message.content
            return response_schema.model_validate_json(content)
        except (
            openai.OpenAIError,
            json.JSONDecodeError,
            ValidationError,
            AttributeError,
            IndexError,
        ) as exc:
            raise LlmUnavailableError(f"LLM call failed: {exc}") from exc

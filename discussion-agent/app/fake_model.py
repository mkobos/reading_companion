"""A deterministic, no-network stand-in model for LLM_BACKEND=fake.

Unlike backend/'s DISCUSSION_AGENT_FAKE (which bypasses calling a
discussion-agent process at all), this replaces only the model inside a
real Agent/Runner invocation — before_agent_callback, tool registration,
and after_model_callback (app/agent.py) all still run for real on every
turn, so it exercises the full untrusted-content wrapping pipeline with no
model, credentials, or network required.
"""

from collections.abc import AsyncGenerator

from google.adk.models import BaseLlm, LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.genai import types

CANNED_TEXT = (
    "[fake model] This is a canned discussion-agent response for local "
    "development and tests. No language model was called."
)


class FakeLlm(BaseLlm):
    model: str = "fake"

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        yield LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=CANNED_TEXT)]
            ),
            partial=False,
        )

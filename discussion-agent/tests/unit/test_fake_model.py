"""Unit tests for app.fake_model.FakeLlm, the LLM_BACKEND=fake stand-in.

Constructs and runs with no network and no credentials: unlike the real
Gemini/LiteLlm backends, FakeLlm never calls out anywhere.
"""

import pytest
from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest

from app.fake_model import CANNED_TEXT, FakeLlm

pytestmark = pytest.mark.asyncio


def _text_of(llm_response) -> str:
    return "".join(part.text or "" for part in llm_response.content.parts)


async def test_is_a_base_llm():
    assert isinstance(FakeLlm(), BaseLlm)


async def test_yields_exactly_one_response_non_streaming():
    responses = [r async for r in FakeLlm().generate_content_async(LlmRequest())]

    assert len(responses) == 1
    assert responses[0].partial is False
    assert _text_of(responses[0]) == CANNED_TEXT


async def test_yields_exactly_one_response_streaming():
    responses = [
        r async for r in FakeLlm().generate_content_async(LlmRequest(), stream=True)
    ]

    assert len(responses) == 1
    assert responses[0].partial is False


async def test_response_text_is_deterministic_across_calls():
    first = [r async for r in FakeLlm().generate_content_async(LlmRequest())]
    second = [r async for r in FakeLlm().generate_content_async(LlmRequest())]

    assert _text_of(first[0]) == _text_of(second[0])


async def test_runs_with_no_gcp_credentials(monkeypatch):
    for credential_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(credential_var, raising=False)

    responses = [r async for r in FakeLlm().generate_content_async(LlmRequest())]

    assert len(responses) == 1

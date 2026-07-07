"""The `web_search` tool (spec/contracts/agent-contract.yaml).

ADK's built-in `google_search` grounding tool cannot be registered alongside
custom function tools on the same LlmAgent (mixing built-in and function
tools is unsupported outside the experimental Interactions API). The
standard workaround: a dedicated sub-agent whose only tool is
`google_search`, invoked here via an internal Runner and re-exposed to the
root agent as a plain function tool, so we keep full control over wrapping
its output as untrusted content.
"""

import uuid
from collections.abc import Callable

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.untrusted import wrap_untrusted

_SEARCH_AGENT_INSTRUCTION = (
    "Answer the query using web search grounding. Report only what search "
    "finds; be concise and factual."
)


def build_web_search_tool() -> Callable:
    """Returns a `web_search(query)` async tool backed by Google Search grounding."""
    from google.adk.tools import google_search

    search_agent = Agent(
        name="web_search_agent",
        model=Gemini(model="gemini-flash-latest"),
        instruction=_SEARCH_AGENT_INSTRUCTION,
        tools=[google_search],
    )
    runner = InMemoryRunner(agent=search_agent, app_name="web_search_agent")

    async def web_search(query: str) -> str:
        """External fact lookup via the provider's search grounding.

        Args:
            query: The search terms.

        Returns:
            Untrusted external text summarizing what the search found.
        """
        user_id = str(uuid.uuid4())
        session = await runner.session_service.create_session(
            app_name="web_search_agent", user_id=user_id
        )
        final_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=query)]),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(part.text or "" for part in event.content.parts)
        return wrap_untrusted(final_text, "tool_result")

    return web_search

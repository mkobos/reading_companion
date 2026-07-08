"""Production-wireable fake for DiscussionAgentClient, gated by an env var.

Unlike tests/conftest.py's FakeDiscussionAgentClient (a scripted test
double used only via pytest fixtures), this one is constructed by
app/main.py's create_app() itself when DISCUSSION_AGENT_FAKE is truthy —
so it must work purely from constructor args, with no test-time scripting
hooks. It exists to let e2e/UI work (pending-state, failure-state) proceed
without a running discussion-agent process or GCP credentials; it never
reads real workspace data or touches discussion-agent's untrusted-content
wrapping, since it replaces the whole agent call rather than any part of
it.
"""

import time

from app.discussion_agent_client import AgentInvocationError, AgentTurnResult

SIMULATE_FAILURE_TOKEN = "__SIMULATE_AGENT_FAILURE__"

_CANNED_RESPONSE_TEXT = "This is a fake discussion-agent response."


class FakeDiscussionAgentClient:
    def __init__(self, *, delay_ms: float = 0) -> None:
        self._delay_seconds = delay_ms / 1000

    def create_session(self, *, session_id: str, user_id: str) -> None:
        pass

    def run_turn(
        self, *, session_id: str, user_id: str, user_message: str, context: dict
    ) -> AgentTurnResult:
        if self._delay_seconds:
            time.sleep(self._delay_seconds)

        if SIMULATE_FAILURE_TOKEN in user_message:
            raise AgentInvocationError("Simulated agent failure (fake client sentinel token).")

        return AgentTurnResult(response_text=_CANNED_RESPONSE_TEXT)

import time

import pytest

from app.discussion_agent_client import AgentInvocationError
from app.fake_discussion_agent_client import SIMULATE_FAILURE_TOKEN, FakeDiscussionAgentClient


def test_create_session_is_a_noop() -> None:
    client = FakeDiscussionAgentClient()

    client.create_session(session_id="s1", user_id="u1")


def test_run_turn_returns_canned_response() -> None:
    client = FakeDiscussionAgentClient()

    result = client.run_turn(
        session_id="s1", user_id="u1", user_message="hello", context={}
    )

    assert result.response_text
    assert result.tool_calls == []


def test_run_turn_delays_by_configured_amount() -> None:
    client = FakeDiscussionAgentClient(delay_ms=200)

    start = time.monotonic()
    client.run_turn(session_id="s1", user_id="u1", user_message="hello", context={})
    elapsed = time.monotonic() - start

    assert elapsed >= 0.1


def test_run_turn_raises_on_sentinel_token() -> None:
    client = FakeDiscussionAgentClient()

    with pytest.raises(AgentInvocationError):
        client.run_turn(
            session_id="s1",
            user_id="u1",
            user_message=f"please fail {SIMULATE_FAILURE_TOKEN} now",
            context={},
        )

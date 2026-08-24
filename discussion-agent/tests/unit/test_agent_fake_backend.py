"""Drives a full discussion-agent turn under LLM_BACKEND=fake.

Unlike backend/'s DISCUSSION_AGENT_FAKE (which never calls a
discussion-agent process at all), this proves that with LLM_BACKEND=fake
the *real* agent machinery still runs end-to-end with no model,
credentials, or network: before_agent_callback (_assemble_incoming_context,
the untrusted-content wrapping entry point) and after_model_callback
(_strip_leaked_untrusted_markup) both fire on a real turn through a real
Runner.
"""

import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import build_discussion_agent
from app.fake_model import CANNED_TEXT


def test_fake_backend_turn_runs_through_the_real_wrapping_pipeline(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "fake")

    agent = build_discussion_agent()
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=agent, session_service=session_service, app_name="test")

    envelope = {
        "user_message": "What does this passage mean?",
        "context": {
            "viewport_text": "some visible text",
            "document_blocks": [],
        },
    }
    message = types.Content(
        role="user", parts=[types.Part.from_text(text=json.dumps(envelope))]
    )
    events = list(
        runner.run(new_message=message, user_id="test_user", session_id=session.id)
    )

    final_text = "".join(
        part.text or ""
        for event in events
        if event.content and event.content.parts
        for part in event.content.parts
    )
    assert CANNED_TEXT in final_text

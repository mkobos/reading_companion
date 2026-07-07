"""Unit tests for app.agent's before_agent_callback, which decodes the wire
envelope a caller (the backend) sends as the turn's message text and
replaces it with the assembled, wrapped context before the model sees it.

This is the integration point documented in
spec/contracts/agent-contract.yaml's discussion_agent.session: the backend
sends raw {"user_message": ..., "context": {...}} as JSON text; this
callback is the sole place that turns it into the model-facing prompt via
app.context_assembly.assemble_context (which owns all untrusted-content
wrapping). No live model call is needed — this only exercises the callback
function directly, mirroring how tests/unit/test_untrusted.py and the
after_model_callback tests exercise app.agent's other callback in isolation.
"""

import json
from types import SimpleNamespace

from google.genai import types

from app.agent import _assemble_incoming_context


def _callback_context(text: str) -> SimpleNamespace:
    content = types.Content(role="user", parts=[types.Part(text=text)])
    return SimpleNamespace(user_content=content)


def test_decodes_envelope_and_replaces_text_with_assembled_context():
    envelope = {
        "user_message": "What does this passage mean?",
        "context": {
            "viewport_text": '<block id="000000">Some document text.</block>',
            "document_metadata": {"filename": "doc.md"},
        },
    }
    ctx = _callback_context(json.dumps(envelope))

    result = _assemble_incoming_context(callback_context=ctx)

    assert result is None
    assembled_text = ctx.user_content.parts[0].text
    assert "Some document text." in assembled_text
    assert "What does this passage mean?" in assembled_text
    assert '<untrusted source="document">' in assembled_text


def test_passthrough_for_plain_text_message():
    ctx = _callback_context("just a plain message, not JSON")

    result = _assemble_incoming_context(callback_context=ctx)

    assert result is None
    assert ctx.user_content.parts[0].text == "just a plain message, not JSON"


def test_passthrough_for_json_missing_the_expected_shape():
    ctx = _callback_context(json.dumps({"foo": "bar"}))

    result = _assemble_incoming_context(callback_context=ctx)

    assert result is None
    assert ctx.user_content.parts[0].text == json.dumps({"foo": "bar"})


def test_assembled_context_places_user_message_after_context():
    envelope = {
        "user_message": "USER_MESSAGE_MARKER",
        "context": {
            "viewport_text": "CONTEXT_MARKER",
            "document_metadata": {},
        },
    }
    ctx = _callback_context(json.dumps(envelope))

    _assemble_incoming_context(callback_context=ctx)

    assembled_text = ctx.user_content.parts[0].text
    assert assembled_text.index("CONTEXT_MARKER") < assembled_text.index(
        "USER_MESSAGE_MARKER"
    )

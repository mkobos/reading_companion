"""pytest-bdd steps for the untagged, deterministic scenarios in
spec/features/discussion.feature.

Only these two scenarios are bound here via named @scenario decorators
(not a blanket `scenarios(path)`) — the file's @eval scenarios are judged by
the eval harness instead and are never given step definitions (see
conftest.py and spec/features/README.md).
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pytest_bdd import given, scenario, then, when

from app.agent import build_discussion_agent
from app.context_assembly import DiscussionContext, HistoryTurn, Note, assemble_context


@scenario(
    "../../../spec/features/discussion.feature", "Agent receives the shared context"
)
def test_agent_receives_the_shared_context():
    pass


@scenario(
    "../../../spec/features/discussion.feature", "Agent answers from context alone"
)
def test_agent_answers_from_context_alone():
    pass


# --- Background (shared by every scenario in the file) ---


@given('workspace "W" contains a parsed document')
def _workspace_has_document():
    # TODO: deliberate no-op — there is no workspace/document store yet
    # (agent-only isolated scope). Neither wired scenario below depends on
    # this Background step's outcome; both build their own DiscussionContext
    # fixture directly. Once a workspace/document layer exists, give this a
    # real body (e.g. create a fixture workspace with a parsed document) if
    # a scenario comes to depend on it. See docs/repo_configuration_progress.md.
    pass


@given("the user is reading with a known viewport")
def _known_viewport():
    # TODO: deliberate no-op, same reason as _workspace_has_document above —
    # no viewport/reading-state layer exists yet for this step to set up.
    pass


# --- Agent receives the shared context ---


@when("the user sends a message in a discussion", target_fixture="assembled_context")
def _send_message_with_full_context():
    # NOTE: "active_discussion" (the current discussion's own prior turns) is
    # intentionally not asserted here — per agent-contract.yaml it is carried
    # by the agent's managed session, not by discussion_context, so it is not
    # something assemble_context() produces.
    context = DiscussionContext(
        viewport_text="VIEWPORT_MARKER: visible text",
        passage_text="MARKED_PASSAGE_MARKER: the anchored passage",
        notes=[
            Note(
                text="RELEVANT_NOTE_MARKER: a nearby note",
                passage_text=None,
                created_at="2026-01-01T00:00:00Z",
            )
        ],
        discussion_history=[
            HistoryTurn(
                user_message="WORKSPACE_HISTORY_MARKER: earlier question",
                agent_response="earlier answer",
                viewport_text="earlier viewport",
            )
        ],
        journal="READING_JOURNAL_MARKER: journal so far",
        document_metadata={"filename": "doc.pdf", "block_count": 1},
    )
    return assemble_context(context)


@then("the agent is provided with a shared context containing:")
def _assert_shared_context_elements_present(assembled_context):
    for marker in (
        "VIEWPORT_MARKER",
        "MARKED_PASSAGE_MARKER",
        "RELEVANT_NOTE_MARKER",
        "WORKSPACE_HISTORY_MARKER",
        "READING_JOURNAL_MARKER",
    ):
        assert marker in assembled_context


# --- Agent answers from context alone ---


@given(
    "the agent can answer the user's message from the shared context alone",
    target_fixture="context_sufficient_message",
)
def _context_sufficient_message():
    return (
        "The visible text says: 'The categorical imperative is Kant's central "
        "ethical principle.' Based only on what's shown above, what does "
        "'categorical imperative' mean?"
    )


@when("the user sends the message", target_fixture="turn_events")
def _run_turn(context_sufficient_message):
    agent = build_discussion_agent(blocks=[])
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="bdd_user", app_name="bdd_test"
    )
    runner = Runner(agent=agent, session_service=session_service, app_name="bdd_test")
    message = types.Content(
        role="user", parts=[types.Part.from_text(text=context_sufficient_message)]
    )
    return list(
        runner.run(new_message=message, user_id="bdd_user", session_id=session.id)
    )


@then("the agent responds without invoking any tool")
def _assert_no_tool_invoked(turn_events):
    has_text_response = any(
        event.content
        and event.content.parts
        and any(part.text for part in event.content.parts)
        for event in turn_events
    )
    assert has_text_response, (
        "expected at least one real text response from a live model call"
    )

    tool_calls = [
        part.function_call
        for event in turn_events
        if event.content and event.content.parts
        for part in event.content.parts
        if part.function_call
    ]
    assert tool_calls == []

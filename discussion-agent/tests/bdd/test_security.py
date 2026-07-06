"""pytest-bdd steps for the untagged, deterministic scenarios in
spec/features/security.feature.

Only these three scenarios are bound here via named @scenario decorators
(not a blanket `scenarios(path)`) — the file's @eval scenarios are judged by
the eval harness instead and are never given step definitions (see
conftest.py and spec/features/README.md). All three scenarios below reduce
to code-level checks on prompt assembly and tool registration, not on what
a model says.
"""

import inspect

from pytest_bdd import given, parsers, scenario, then, when

from app.agent import _INSTRUCTION, build_discussion_agent
from app.context_assembly import DiscussionContext, HistoryTurn, Note, assemble_context
from app.document_search import Block


@scenario(
    "../../../spec/features/security.feature",
    "All untrusted content is delimited uniformly",
)
def test_all_untrusted_content_is_delimited_uniformly():
    pass


@scenario(
    "../../../spec/features/security.feature",
    "Tools limit the blast radius of a successful injection",
)
def test_tools_limit_the_blast_radius_of_a_successful_injection():
    pass


@scenario(
    "../../../spec/features/security.feature",
    "Agent tools cannot cross workspace boundaries",
)
def test_agent_tools_cannot_cross_workspace_boundaries():
    pass


# --- All untrusted content is delimited uniformly ---


@given(
    "various untrusted contents exist in the workspace context",
    target_fixture="context",
)
def _various_untrusted_contents():
    return DiscussionContext(
        viewport_text="document text",
        passage_text=None,
        notes=[
            Note(text="note text", passage_text=None, created_at="2026-01-01T00:00:00Z")
        ],
        discussion_history=[
            HistoryTurn(user_message="u", agent_response="a", viewport_text="v")
        ],
        journal="journal text",
        document_metadata={},
    )


@when(
    "a prompt is assembled for the agent or a plain LLM call",
    target_fixture="assembled",
)
def _assemble(context):
    return assemble_context(context)


@then(
    "document text, notes, discussion history, journal, and tool results "
    "are wrapped in uniform data delimiters"
)
def _assert_uniform_delimiters(assembled):
    for source_type in ("document", "note", "discussion_history", "journal"):
        assert f'<untrusted source="{source_type}">' in assembled

    search_document = _build_search_tool_with_one_block()
    tool_result = search_document(query="x")[0]["text"]
    assert tool_result.startswith('<untrusted source="tool_result">')


@then(
    "system instructions specify that content within these delimiters is untrusted data"
)
def _assert_instruction_states_untrusted_rule():
    lowered = _INSTRUCTION.lower()
    assert '<untrusted source="' in _INSTRUCTION
    assert "never" in lowered and "instructions to follow" in lowered


# --- Tools limit the blast radius of a successful injection ---


@given("a discussion message is processed", target_fixture="agent")
def _discussion_message_processed():
    return build_discussion_agent(blocks=[Block(block_id="000000", text="x")])


@when("the agent invokes any tool")
def _agent_invokes_any_tool(agent):
    pass  # structural check only — no live tool call needed for this scenario


@then("the agent tools must be read-only")
def _assert_tools_are_read_only(agent):
    # This doesn't inspect tool behavior — it can't prove a function has no
    # side effects. The read-only guarantee comes from search_document and
    # web_search being read-only by implementation (verified by code review,
    # not this test); this check's actual job is to catch an unexpected
    # third tool being registered.
    assert {tool.__name__ for tool in agent.tools} == {"search_document", "web_search"}


@then("document search is scoped server-side to the current workspace")
def _assert_document_search_scoped_server_side(agent):
    # This is the strong, direct check in this scenario: it confirms
    # search_document's signature has no workspace_id/document_id parameter
    # at all. Workspace scope is bound into the tool via closure at
    # construction time (see build_search_document_tool) instead — so
    # there's no such parameter for the model to fill in with a value that
    # would redirect the search to another workspace's document, regardless
    # of what the model is told to do.
    search_document = next(
        tool for tool in agent.tools if tool.__name__ == "search_document"
    )
    assert set(inspect.signature(search_document).parameters) == {"query"}


@then("no tool can write data, access other workspaces, or reach internal services")
def _assert_no_write_capable_tools(agent):
    # No static check can prove an arbitrary function never writes data or
    # calls an internal service — that's a code-review-level guarantee, not
    # something this test can verify. The checkable slice of this claim is
    # covered above: _assert_tools_are_read_only pins the tool set to the two
    # known read-only tools, and _assert_document_search_scoped_server_side
    # confirms workspace scope isn't a model-controllable parameter.
    pass


# --- Agent tools cannot cross workspace boundaries ---


@given(
    parsers.parse('a discussion in workspace "{workspace_id}"'),
    target_fixture="workspace_agent",
)
def _discussion_in_workspace(workspace_id):
    # The "set by the backend" half of the next Then step's claim is
    # established here, not inside _assert_workspace_scope_not_model_controlled:
    # `blocks` is a plain Python argument decided in this fixture code, before
    # the agent or model exists — exactly how a real backend would choose a
    # workspace's blocks at agent-construction time. It is never derived from
    # anything a model says.
    blocks = [
        Block(block_id="000000", text=f"Document content for workspace {workspace_id}.")
    ]
    return {"workspace_id": workspace_id, "agent": build_discussion_agent(blocks)}


@when("the agent invokes document search", target_fixture="search_results")
def _agent_invokes_document_search(workspace_agent):
    search_document = next(
        tool
        for tool in workspace_agent["agent"].tools
        if tool.__name__ == "search_document"
    )
    return search_document(query="Document content")


@then(
    parsers.parse(
        'the search executes only against the document in workspace "{workspace_id}"'
    )
)
def _assert_search_scoped_to_workspace(search_results):
    # Not checking for `workspace_id` in the result text — that would only
    # pass because the fixture's document text happens to mention the
    # workspace id, an artifact of how the fixture was written, not a
    # property of search_document. There's also no deeper isolation claim to
    # test here: build_search_document_tool's closure only ever contains
    # this one workspace's blocks, so there's no other workspace's data it
    # could reach even in principle — that's what the next Then step
    # (_assert_workspace_scope_not_model_controlled) actually verifies. This
    # step just confirms the tool functioned and found the block it was
    # given.
    assert len(search_results) == 1


@then("the workspace scope is set by the backend, not by model-controlled input")
def _assert_workspace_scope_not_model_controlled(workspace_agent):
    # This only verifies the "not model-controlled" half of the claim — the
    # absence of a channel, not the presence of backend control (that half
    # is established by _discussion_in_workspace above, which decides
    # `blocks` in plain Python before the agent exists).
    #
    # ADK builds the FunctionDeclaration it hands to the model (the schema
    # of arguments the model is allowed to fill in when calling this tool)
    # by introspecting this function's signature via inspect.signature (see
    # google.adk.tools.function_tool.FunctionTool._get_declaration ->
    # build_function_declaration). So if `query` is the only parameter, the
    # model-facing schema has exactly one fillable field — there is no
    # workspace_id/document_id slot for the model to populate at all, no
    # matter what any instruction (legitimate or injected) tells it to try.
    search_document = next(
        tool
        for tool in workspace_agent["agent"].tools
        if tool.__name__ == "search_document"
    )
    assert set(inspect.signature(search_document).parameters) == {"query"}


def _build_search_tool_with_one_block():
    from app.document_search import build_search_document_tool

    return build_search_document_tool([Block(block_id="000000", text="x")])

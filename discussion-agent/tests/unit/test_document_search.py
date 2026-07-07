"""Unit tests for app.document_search.build_search_document_tool.

Binds spec/features/security.feature's untagged scenarios "Tools limit the
blast radius of a successful injection" and "Agent tools cannot cross
workspace boundaries" — the tool's real ADK FunctionDeclaration (the
model-facing schema, not just its Python signature) is inspected below to
confirm workspace scope is not a model-controllable parameter; see
tests/bdd/ for how this same assertion is reused as pytest-bdd steps.

Blocks now reach the tool via ToolContext.state (populated per-turn by
app.agent._assemble_incoming_context from the wire envelope's
document_blocks field) rather than a construction-time closure — see
spec/contracts/agent-contract.yaml's search_document.scoping. Tests below
use a bare SimpleNamespace as a fake ToolContext, matching this repo's
existing fake-context idiom in tests/unit/test_incoming_context.py.
"""

from types import SimpleNamespace

from google.adk.tools.function_tool import FunctionTool

from app.document_search import build_search_document_tool

_BLOCK_DICTS = [
    {
        "block_id": "000000",
        "text": "The categorical imperative is a central concept in Kantian ethics.",
    },
    {
        "block_id": "000001",
        "text": "Rawls introduced the veil of ignorance as a thought experiment.",
    },
]


def _tool_context(document_blocks: list[dict]) -> SimpleNamespace:
    return SimpleNamespace(state={"document_blocks": document_blocks})


def test_matching_query_returns_wrapped_results_with_block_id_and_score():
    search_document = build_search_document_tool()

    results = search_document(
        query="categorical imperative", tool_context=_tool_context(_BLOCK_DICTS)
    )["results"]

    assert len(results) == 1
    result = results[0]
    assert result["block_id"] == "000000"
    assert result["text"].startswith('<untrusted source="tool_result">')
    assert "categorical imperative" in result["text"]
    assert isinstance(result["score"], float)
    assert result["score"] > 0


def test_no_match_returns_empty_list_and_never_raises():
    search_document = build_search_document_tool()

    results = search_document(
        query="quantum entanglement", tool_context=_tool_context(_BLOCK_DICTS)
    )["results"]

    assert results == []


def test_query_with_fts5_special_characters_does_not_raise():
    search_document = build_search_document_tool()

    # Unbalanced quote and a bare wildcard are syntactically meaningful to
    # FTS5's own query language; the tool must neutralize that (e.g. treat
    # the query as a literal phrase) rather than let a malformed MATCH
    # expression raise back through the tool.
    results = search_document(
        query='unterminated " quote * and () parens',
        tool_context=_tool_context(_BLOCK_DICTS),
    )["results"]

    assert results == []


def test_model_facing_declaration_exposes_only_query_no_workspace_scope():
    search_document = build_search_document_tool()

    declaration = FunctionTool(search_document)._get_declaration()

    assert set(declaration.parameters_json_schema["properties"]) == {"query"}


def test_empty_document_returns_no_results_without_error():
    search_document = build_search_document_tool()

    assert search_document(query="anything", tool_context=_tool_context([]))["results"] == []


def test_missing_document_blocks_state_returns_no_results_without_error():
    search_document = build_search_document_tool()

    assert (
        search_document(query="anything", tool_context=SimpleNamespace(state={}))["results"]
        == []
    )

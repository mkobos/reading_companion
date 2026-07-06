"""Unit tests for app.document_search.build_search_document_tool.

Binds spec/features/security.feature's untagged scenarios "Tools limit the
blast radius of a successful injection" and "Agent tools cannot cross
workspace boundaries" — the tool's callable signature is inspected below to
confirm workspace scope is not a model-controllable parameter; see
tests/bdd/ for how this same assertion is reused as pytest-bdd steps.
"""

import inspect

from app.document_search import Block, build_search_document_tool

_BLOCKS = [
    Block(
        block_id="000000",
        text="The categorical imperative is a central concept in Kantian ethics.",
    ),
    Block(
        block_id="000001",
        text="Rawls introduced the veil of ignorance as a thought experiment.",
    ),
]


def test_matching_query_returns_wrapped_results_with_block_id_and_score():
    search_document = build_search_document_tool(_BLOCKS)

    results = search_document(query="categorical imperative")

    assert len(results) == 1
    result = results[0]
    assert result["block_id"] == "000000"
    assert result["text"].startswith('<untrusted source="tool_result">')
    assert "categorical imperative" in result["text"]
    assert isinstance(result["score"], float)
    assert result["score"] > 0


def test_no_match_returns_empty_list_and_never_raises():
    search_document = build_search_document_tool(_BLOCKS)

    results = search_document(query="quantum entanglement")

    assert results == []


def test_query_with_fts5_special_characters_does_not_raise():
    search_document = build_search_document_tool(_BLOCKS)

    # Unbalanced quote and a bare wildcard are syntactically meaningful to
    # FTS5's own query language; the tool must neutralize that (e.g. treat
    # the query as a literal phrase) rather than let a malformed MATCH
    # expression raise back through the tool.
    results = search_document(query='unterminated " quote * and () parens')

    assert results == []


def test_tool_signature_exposes_only_query_no_workspace_scope():
    search_document = build_search_document_tool(_BLOCKS)

    params = inspect.signature(search_document).parameters
    assert set(params) == {"query"}


def test_empty_document_returns_no_results_without_error():
    search_document = build_search_document_tool([])

    assert search_document(query="anything") == []

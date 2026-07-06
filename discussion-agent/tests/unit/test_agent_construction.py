"""Unit tests for app.agent.build_discussion_agent's tool registration.

Binds spec/features/security.feature's untagged scenario "Tools limit the
blast radius of a successful injection" (constraints.read_only /
no_write_tools in spec/contracts/agent-contract.yaml) — no live model call
needed, this is purely a structural check on what's registered.
"""

import inspect

from app.agent import build_discussion_agent
from app.document_search import Block

_BLOCKS = [Block(block_id="000000", text="Some document text.")]

_WRITE_VERBS = ("write", "delete", "update", "create", "modify", "put", "post", "save")


def test_registers_exactly_the_two_read_only_tools():
    agent = build_discussion_agent(_BLOCKS)

    tool_names = {tool.__name__ for tool in agent.tools}
    assert tool_names == {"search_document", "web_search"}


def test_no_registered_tool_looks_write_capable_by_name():
    agent = build_discussion_agent(_BLOCKS)

    for tool in agent.tools:
        lowered = tool.__name__.lower()
        assert not any(verb in lowered for verb in _WRITE_VERBS)


def test_no_registered_tool_exposes_a_workspace_or_document_id_parameter():
    agent = build_discussion_agent(_BLOCKS)

    for tool in agent.tools:
        params = set(inspect.signature(tool).parameters)
        assert "workspace_id" not in params
        assert "document_id" not in params

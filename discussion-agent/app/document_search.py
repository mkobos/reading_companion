"""The `search_document` tool (spec/contracts/agent-contract.yaml).

Per spec/technical_specification.md §8, builds an ephemeral in-memory SQLite
FTS5 index on every call rather than maintaining a persistent one. The
workspace's blocks are bound into the tool via closure at construction time
(never a model-controllable argument), so the model has no way to target
another workspace's document.
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from app.untrusted import wrap_untrusted


@dataclass
class Block:
    block_id: str
    text: str


def build_search_document_tool(blocks: list[Block]) -> Callable[[str], dict]:
    """Returns a `search_document(query)` tool scoped to `blocks`."""

    def search_document(query: str) -> dict:
        """Keyword search over all blocks of this workspace's document.

        Args:
            query: The search terms.

        Returns:
            `{"results": [...]}`, a list of matching blocks (block_id, text,
            score), highest score first. Empty if nothing matches.

            A plain dict rather than a dataclass: this return value is
            terminal — ADK hands it straight to
            `types.Part.from_function_response`, which requires a plain
            JSON-serializable structure (see
            `google.adk.flows.llm_flows.functions.__build_response_event`,
            "Specs requires the result to be a dict"). If we used a
            dataclass, it would need converting back to a dict before
            returning anyway, and this shape matches agent-contract.yaml's
            `search_document.output.results` JSON Schema field-for-field —
            returning the bare list would instead get silently rewrapped by
            ADK as `{"result": [...]}` (singular), diverging from the
            contract.
        """
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute(
                "CREATE VIRTUAL TABLE blocks USING fts5(block_id UNINDEXED, text)"
            )
            conn.executemany(
                "INSERT INTO blocks (block_id, text) VALUES (?, ?)",
                [(block.block_id, block.text) for block in blocks],
            )
            # Treat the query as a single literal phrase (doubling embedded
            # quotes per SQL string-literal escaping) so caller-supplied text
            # is never parsed as FTS5 query syntax (AND/OR/NOT/*/parens).
            phrase = '"' + query.replace('"', '""') + '"'
            try:
                rows = conn.execute(
                    "SELECT block_id, text, bm25(blocks) AS rank FROM blocks "
                    "WHERE blocks MATCH ? ORDER BY rank",
                    (phrase,),
                ).fetchall()
            except sqlite3.OperationalError:
                return {"results": []}
        finally:
            conn.close()

        return {
            "results": [
                {
                    "block_id": block_id,
                    "text": wrap_untrusted(text, "tool_result"),
                    "score": -rank,
                }
                for block_id, text, rank in rows
            ]
        }

    return search_document

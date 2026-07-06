"""Deterministic untrusted-content wrapping.

Implements the envelope from spec/contracts/agent-contract.yaml's
untrusted_content_wrapping. This is plain string assembly — no LLM call is
involved. Callers apply wrap_untrusted() to a value before it is placed
anywhere in a prompt; the model only ever sees already-wrapped text.
"""

# Mirrors agent-contract.yaml's untrusted_content_wrapping.source_types.
SOURCE_TYPES = frozenset(
    {"document", "passage", "note", "discussion_history", "journal", "tool_result"}
)

# Neutralizes a literal "</untrusted" occurrence in untrusted content so it
# cannot prematurely close its own envelope. A zero-width space breaks the
# contiguous substring without altering how the text reads to a human or a
# model reasoning about it as data.
_ESCAPE_MARKER = "​"


def wrap_untrusted(content: str, source_type: str) -> str:
    """Wraps `content` in a typed `<untrusted>` data section.

    Raises ValueError if `source_type` is not one of the contract's
    documented source_types.
    """
    if source_type not in SOURCE_TYPES:
        raise ValueError(
            f"Unknown untrusted source_type: {source_type!r}; must be one of {sorted(SOURCE_TYPES)}"
        )

    escaped = content.replace("</untrusted", f"<{_ESCAPE_MARKER}/untrusted")
    return f'<untrusted source="{source_type}">\n{escaped}\n</untrusted>'

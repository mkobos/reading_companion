"""Deterministic untrusted-content wrapping.

Implements the envelope from spec/contracts/agent-contract.yaml's
untrusted_content_wrapping. This is plain string assembly — no LLM call is
involved. Callers apply wrap_untrusted() to a value before it is placed
anywhere in a prompt; the model only ever sees already-wrapped text.
strip_untrusted_markup() implements the same contract's
output_sanitization: the reverse direction, deterministically removing the
envelope's tags from model output regardless of whether the model complied
with the instruction not to reproduce them.

A byte-for-byte port of discussion-agent/app/untrusted.py: the two AI-call
families (the agent, and backend's plain suggestions/journal calls) are
separate deployable packages with no shared library, but both must honor the
same contract, so the logic is duplicated rather than shared.
"""

import re

# Mirrors agent-contract.yaml's untrusted_content_wrapping.source_types.
SOURCE_TYPES = frozenset(
    {"document", "passage", "note", "discussion_history", "journal", "tool_result"}
)

# Matches only the tags wrap_untrusted() itself produces (a `source="..."`
# attribute, no escape marker), not an escaped `</untrusted` occurrence
# preserved literally inside wrapped content by the escaping below.
_ENVELOPE_TAG_RE = re.compile(r'<untrusted source="[^"]*">\n?|\n?</untrusted>')

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


def strip_untrusted_markup(text: str) -> str:
    """Removes any `<untrusted source="...">`/`</untrusted>` tags from `text`.

    De-envelopes rather than deletes: the inner content is left in place.
    Deleting the whole block risks leaving an empty response if the model
    never restates the content in its own words, which is worse than a
    de-enveloped (but still present) leak. A model-generated envelope tag is
    always well-formed (it can only contain a `source="..."` attribute with
    no escape marker — see wrap_untrusted's escaping), so this plain regex
    is sufficient; it cannot match an escaped `</untrusted` occurrence that
    was preserved literally inside wrapped content.
    """
    return _ENVELOPE_TAG_RE.sub("", text)

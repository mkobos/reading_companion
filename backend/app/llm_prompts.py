"""Prompt assembly for backend's two plain LLM calls (suggestions, journal).

Mirrors discussion-agent/app/context_assembly.py's section-template/wrapping
style: every piece of untrusted text is passed through wrap_untrusted before
it is placed in the prompt, per spec/contracts/agent-contract.yaml's
untrusted_content_wrapping.
"""

from app.store import Note, Turn
from app.untrusted import wrap_untrusted

# agent-contract.yaml's journal_call: "If full history exceeds 100,000
# characters (hard limit), truncate oldest-first; previous journal carries
# memory of what's dropped."
_JOURNAL_CONTENT_CHAR_LIMIT = 100_000


def build_suggestions_prompt(viewport_text: str, passage_text: str) -> str:
    sections = [
        "Viewport:",
        wrap_untrusted(viewport_text, "document"),
        "Marked passage:",
        wrap_untrusted(passage_text, "passage"),
    ]
    return "\n\n".join(sections)


def _turn_text(turn: Turn, viewport_text: str) -> str:
    return (
        f"User: {turn.user_message}\n"
        f"Agent: {turn.agent_response}\n"
        f"Viewport at the time: {viewport_text}"
    )


def build_journal_prompt(
    notes: list[Note],
    turns: list[tuple[Turn, str]],
    previous_journal: str | None,
    document_metadata: dict,
) -> str:
    """`turns` pairs each Turn with its viewport's resolved text (the router
    resolves this from the document's blocks, same as
    discussions.py's _history_context)."""
    sections: list[str] = []

    if notes:
        sections.append("Notes, in document order:")
        for note in notes:
            sections.append(wrap_untrusted(note.text, "note"))

    if turns:
        sections.append("All discussion turns, in creation order:")
        for turn, viewport_text in turns:
            sections.append(wrap_untrusted(_turn_text(turn, viewport_text), "discussion_history"))

    if previous_journal is not None:
        sections += ["Previous journal:", wrap_untrusted(previous_journal, "journal")]

    sections += ["Document metadata:", str(document_metadata)]

    return "\n\n".join(sections)


def truncate_journal_inputs(
    notes: list[Note], turns: list[tuple[Turn, str]], limit: int = _JOURNAL_CONTENT_CHAR_LIMIT
) -> tuple[list[Note], list[tuple[Turn, str]]]:
    """Drops the oldest notes/turns (merged by created_at) until the combined
    text length is under `limit`. The previous journal and document metadata
    are never truncated — the contract relies on the previous journal to
    carry memory of whatever gets dropped here."""

    items = sorted(
        [("note", note) for note in notes] + [("turn", turn) for turn in turns],
        key=lambda pair: (pair[1][0] if pair[0] == "turn" else pair[1]).created_at,
    )
    total = sum(_content_length(kind, item) for kind, item in items)
    while total > limit and items:
        kind, item = items.pop(0)
        total -= _content_length(kind, item)

    kept_notes = [item for kind, item in items if kind == "note"]
    kept_turns = [item for kind, item in items if kind == "turn"]
    return kept_notes, kept_turns


def _content_length(kind: str, item) -> int:
    if kind == "note":
        return len(item.text)
    turn, viewport_text = item
    return len(turn.user_message) + len(turn.agent_response) + len(viewport_text)

"""Assembles a discussion turn's input text from the discussion_context
envelope (spec/contracts/agent-contract.yaml's `discussion_context`).

The backend passes raw, unwrapped field text; this module is the agent's
sole point of untrusted-content wrapping for its incoming context.
"""

from dataclasses import dataclass, field

from app.untrusted import wrap_untrusted


@dataclass
class Note:
    text: str
    passage_text: str | None
    created_at: str


@dataclass
class HistoryTurn:
    user_message: str
    agent_response: str
    viewport_text: str


@dataclass
class DiscussionContext:
    viewport_text: str
    passage_text: str | None = None
    notes: list[Note] = field(default_factory=list)
    discussion_history: list[HistoryTurn] = field(default_factory=list)
    journal: str | None = None
    document_metadata: dict = field(default_factory=dict)


def assemble_context(context: DiscussionContext) -> str:
    """Renders `context` as labeled sections, wrapping every untrusted field.

    Returns plain text rather than JSON: this output is terminal — it goes
    straight into the model's prompt and nothing in this codebase parses it
    back — so a structured format would only add escaping complexity (e.g.
    JSON-string-escaping on top of the `</untrusted` escaping already done
    by wrap_untrusted) without a corresponding benefit. It also matches
    agent-contract.yaml's untrusted_content_wrapping.envelope, which
    specifies this exact plain-text template.
    """
    sections = [
        "Viewport:",
        wrap_untrusted(context.viewport_text, "document"),
    ]

    if context.passage_text is not None:
        sections += [
            "Marked passage:",
            wrap_untrusted(context.passage_text, "passage"),
        ]

    if context.notes:
        sections.append("Notes nearest to the anchor:")
        for note in context.notes:
            sections.append(wrap_untrusted(note.text, "note"))

    if context.discussion_history:
        sections.append("Recent turns from other discussions in this workspace:")
        for turn in context.discussion_history:
            turn_text = (
                f"User: {turn.user_message}\n"
                f"Agent: {turn.agent_response}\n"
                f"Viewport at the time: {turn.viewport_text}"
            )
            sections.append(wrap_untrusted(turn_text, "discussion_history"))

    if context.journal is not None:
        sections += [
            "Reading journal:",
            wrap_untrusted(context.journal, "journal"),
        ]

    sections += [
        "Document metadata:",
        str(context.document_metadata),
    ]

    return "\n\n".join(sections)

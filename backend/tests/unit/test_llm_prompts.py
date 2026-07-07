"""Unit tests for app.llm_prompts: wrapping correctness (binds
security.feature's "All untrusted content is delimited uniformly" for
backend's plain LLM calls) and the journal_call 100k-char truncation rule
from agent-contract.yaml."""

from datetime import datetime, timezone

from app.llm_prompts import build_journal_prompt, build_suggestions_prompt, truncate_journal_inputs
from app.passages import Passage
from app.store import Note, Turn
from app.viewport import Viewport

_NOW = datetime(2026, 7, 7, tzinfo=timezone.utc)


def _passage(text: str = "anchor text") -> Passage:
    return Passage(
        first_block_id="000000",
        first_block_offset=0,
        last_block_id="000000",
        last_block_offset=len(text),
        text=text,
    )


def _note(text: str, created_at: datetime = _NOW) -> Note:
    return Note(note_id="n1", anchor=_passage(), text=text, created_at=created_at, updated_at=created_at)


def _turn(user_message: str, agent_response: str, created_at: datetime = _NOW, turn_id: str = "t1") -> Turn:
    return Turn(
        turn_id=turn_id,
        user_message=user_message,
        agent_response=agent_response,
        viewport=Viewport(first_block_id="000000", last_block_id="000001"),
        created_at=created_at,
    )


def test_build_suggestions_prompt_wraps_viewport_and_passage():
    prompt = build_suggestions_prompt("visible text", "marked passage text")

    assert '<untrusted source="document">\nvisible text\n</untrusted>' in prompt
    assert '<untrusted source="passage">\nmarked passage text\n</untrusted>' in prompt


def test_build_journal_prompt_wraps_notes_turns_and_previous_journal():
    prompt = build_journal_prompt(
        notes=[_note("A note about Kant.")],
        turns=[(_turn("What is duty?", "Duty is..."), "viewport text")],
        previous_journal="Prior synthesis.",
        document_metadata={"filename": "kant.md", "block_count": 3},
    )

    assert '<untrusted source="note">\nA note about Kant.\n</untrusted>' in prompt
    assert '<untrusted source="discussion_history">' in prompt
    assert "What is duty?" in prompt
    assert '<untrusted source="journal">\nPrior synthesis.\n</untrusted>' in prompt
    assert "kant.md" in prompt


def test_build_journal_prompt_omits_previous_journal_section_when_none():
    prompt = build_journal_prompt(
        notes=[], turns=[], previous_journal=None, document_metadata={"filename": "x", "block_count": 0}
    )

    assert "journal" not in prompt.lower() or "Previous journal" not in prompt


def test_truncate_keeps_everything_under_the_limit():
    notes = [_note("short note")]
    turns = [(_turn("hi", "hello"), "vp")]

    kept_notes, kept_turns = truncate_journal_inputs(notes, turns, limit=100_000)

    assert kept_notes == notes
    assert kept_turns == turns


def test_truncate_drops_oldest_first_until_under_the_limit():
    older_note = _note("x" * 60, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer_turn = (
        _turn("y" * 60, "z" * 60, created_at=datetime(2026, 2, 1, tzinfo=timezone.utc)),
        "vp",
    )

    kept_notes, kept_turns = truncate_journal_inputs([older_note], [newer_turn], limit=150)

    assert kept_notes == []
    assert kept_turns == [newer_turn]

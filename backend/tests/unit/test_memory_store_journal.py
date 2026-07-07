from datetime import datetime, timedelta, timezone

import pytest

from app.store import (
    Discussion,
    Journal,
    JournalNotFoundError,
    Turn,
    Workspace,
    WorkspaceNotFoundError,
)
from app.store.memory_store import InMemoryWorkspaceStore
from app.viewport import Viewport

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_VIEWPORT = Viewport(first_block_id="000000", last_block_id="000000")


def _store_with_workspace(workspace_id: str = "ws1") -> InMemoryWorkspaceStore:
    store = InMemoryWorkspaceStore()
    store.create_workspace(Workspace(workspace_id=workspace_id, created_at=_NOW))
    return store


def _turn(turn_id: str, created_at: datetime) -> Turn:
    return Turn(
        turn_id=turn_id,
        user_message="hi",
        agent_response="hello",
        viewport=_VIEWPORT,
        created_at=created_at,
    )


def test_has_journal_false_until_put():
    store = _store_with_workspace()
    assert store.has_journal("ws1") is False

    store.put_journal("ws1", Journal(text="Some synthesis.", generated_at=_NOW))

    assert store.has_journal("ws1") is True


def test_get_journal_raises_when_none_generated_yet():
    store = _store_with_workspace()
    with pytest.raises(JournalNotFoundError):
        store.get_journal("ws1")


def test_put_journal_raises_when_workspace_missing():
    store = InMemoryWorkspaceStore()
    with pytest.raises(WorkspaceNotFoundError):
        store.put_journal("ws1", Journal(text="x", generated_at=_NOW))


def test_put_journal_overwrites_previous():
    store = _store_with_workspace()
    store.put_journal("ws1", Journal(text="First.", generated_at=_NOW))
    store.put_journal("ws1", Journal(text="Second.", generated_at=_NOW + timedelta(minutes=1)))

    assert store.get_journal("ws1").text == "Second."


def test_delete_workspace_removes_journal():
    store = _store_with_workspace()
    store.put_journal("ws1", Journal(text="Some synthesis.", generated_at=_NOW))

    store.delete_workspace("ws1")
    store.create_workspace(Workspace(workspace_id="ws1", created_at=_NOW))

    assert store.has_journal("ws1") is False


def test_list_all_turns_merges_across_discussions_oldest_first():
    store = _store_with_workspace()
    d1 = Discussion(discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="a")
    d2 = Discussion(
        discussion_id="d2",
        created_at=_NOW + timedelta(minutes=1),
        turn_count=1,
        first_message_preview="b",
    )
    store.create_discussion("ws1", d1, _turn("t1", _NOW + timedelta(minutes=5)))
    store.create_discussion("ws1", d2, _turn("t2", _NOW + timedelta(minutes=2)))
    store.append_turn("ws1", "d1", _turn("t3", _NOW + timedelta(minutes=10)))

    turns = store.list_all_turns("ws1")

    assert [t.turn_id for t in turns] == ["t2", "t1", "t3"]


def test_list_all_turns_raises_when_workspace_missing():
    store = InMemoryWorkspaceStore()
    with pytest.raises(WorkspaceNotFoundError):
        store.list_all_turns("ws1")

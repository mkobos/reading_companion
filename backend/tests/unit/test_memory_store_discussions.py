from datetime import datetime, timedelta, timezone

import pytest

from app.store import (
    Discussion,
    DiscussionNotFoundError,
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


def test_create_discussion_persists_discussion_and_first_turn():
    store = _store_with_workspace()
    discussion = Discussion(
        discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="hi"
    )
    store.create_discussion("ws1", discussion, _turn("t1", _NOW))

    fetched, turns = store.get_discussion("ws1", "d1")
    assert fetched == discussion
    assert [t.turn_id for t in turns] == ["t1"]


def test_get_discussion_raises_when_missing():
    store = _store_with_workspace()
    with pytest.raises(DiscussionNotFoundError):
        store.get_discussion("ws1", "missing")


def test_create_discussion_raises_when_workspace_missing():
    store = InMemoryWorkspaceStore()
    discussion = Discussion(
        discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="hi"
    )
    with pytest.raises(WorkspaceNotFoundError):
        store.create_discussion("ws1", discussion, _turn("t1", _NOW))


def test_append_turn_increments_turn_count_and_orders_turns():
    store = _store_with_workspace()
    discussion = Discussion(
        discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="hi"
    )
    store.create_discussion("ws1", discussion, _turn("t1", _NOW))
    store.append_turn("ws1", "d1", _turn("t2", _NOW + timedelta(minutes=1)))

    fetched, turns = store.get_discussion("ws1", "d1")
    assert fetched.turn_count == 2
    assert [t.turn_id for t in turns] == ["t1", "t2"]


def test_list_discussions_ordered_by_created_at():
    store = _store_with_workspace()
    d1 = Discussion(discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="a")
    d2 = Discussion(
        discussion_id="d2",
        created_at=_NOW + timedelta(minutes=1),
        turn_count=1,
        first_message_preview="b",
    )
    store.create_discussion("ws1", d2, _turn("t2", d2.created_at))
    store.create_discussion("ws1", d1, _turn("t1", d1.created_at))

    assert [d.discussion_id for d in store.list_discussions("ws1")] == ["d1", "d2"]


def test_count_discussions():
    store = _store_with_workspace()
    assert store.count_discussions("ws1") == 0
    store.create_discussion(
        "ws1",
        Discussion(discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="a"),
        _turn("t1", _NOW),
    )
    assert store.count_discussions("ws1") == 1


def test_list_recent_turns_excludes_given_discussion_and_merges_across_discussions():
    store = _store_with_workspace()
    d1 = Discussion(discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="a")
    d2 = Discussion(
        discussion_id="d2",
        created_at=_NOW + timedelta(minutes=1),
        turn_count=1,
        first_message_preview="b",
    )
    store.create_discussion("ws1", d1, _turn("t1-old", _NOW))
    store.append_turn("ws1", "d1", _turn("t1-new", _NOW + timedelta(minutes=5)))
    store.create_discussion("ws1", d2, _turn("t2-old", _NOW + timedelta(minutes=2)))
    store.append_turn("ws1", "d2", _turn("t2-new", _NOW + timedelta(minutes=6)))

    recent = store.list_recent_turns("ws1", exclude_discussion_id="d1", limit=2)

    assert [t.turn_id for t in recent] == ["t2-new", "t2-old"]


def test_list_recent_turns_merge_sorts_newest_first_across_discussions():
    store = _store_with_workspace()
    d1 = Discussion(discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="a")
    d2 = Discussion(
        discussion_id="d2",
        created_at=_NOW + timedelta(minutes=1),
        turn_count=1,
        first_message_preview="b",
    )
    d3 = Discussion(
        discussion_id="d3",
        created_at=_NOW + timedelta(minutes=2),
        turn_count=1,
        first_message_preview="c",
    )
    store.create_discussion("ws1", d1, _turn("t1", _NOW + timedelta(minutes=10)))
    store.create_discussion("ws1", d2, _turn("t2", _NOW + timedelta(minutes=20)))
    store.create_discussion("ws1", d3, _turn("t3", _NOW + timedelta(minutes=15)))

    recent = store.list_recent_turns("ws1", exclude_discussion_id="does-not-exist", limit=2)

    assert [t.turn_id for t in recent] == ["t2", "t3"]


def test_delete_workspace_removes_discussions():
    store = _store_with_workspace()
    store.create_discussion(
        "ws1",
        Discussion(discussion_id="d1", created_at=_NOW, turn_count=1, first_message_preview="a"),
        _turn("t1", _NOW),
    )
    store.delete_workspace("ws1")
    store.create_workspace(Workspace(workspace_id="ws1", created_at=_NOW))

    assert store.list_discussions("ws1") == []

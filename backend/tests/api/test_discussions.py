from app.discussion_agent_client import AgentTurnResult, ToolCallSummary


def _create_workspace_with_document(client, text: bytes = b"Hello world. Second sentence.") -> str:
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]
    client.post(
        f"/api/workspaces/{workspace_id}/document",
        files={"file": ("notes.txt", text, "text/plain")},
    )
    return workspace_id


def _viewport() -> dict:
    return {"first_block_id": "000000", "last_block_id": "000000"}


def _anchor(text: str = "Hello world.") -> dict:
    return {
        "first_block_id": "000000",
        "first_block_offset": 0,
        "last_block_id": "000000",
        "last_block_offset": len(text),
        "text": text,
    }


def test_create_discussion_returns_201_with_first_turn(client, discussion_agent_client):
    discussion_agent_client.next_result = AgentTurnResult(response_text="It means X.")
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "What does this mean?", "viewport": _viewport(), "anchor": _anchor()},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["anchor"]["text"] == "Hello world."
    assert len(body["turns"]) == 1
    assert body["turns"][0]["user_message"] == "What does this mean?"
    assert body["turns"][0]["agent_response"] == "It means X."


def test_create_discussion_without_anchor_is_allowed(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Tell me about this.", "viewport": _viewport()},
    )

    assert response.status_code == 201
    assert response.json()["anchor"] is None


def test_create_discussion_calls_agent_with_session_scoped_to_workspace_and_discussion(
    client, discussion_agent_client
):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )
    discussion_id = response.json()["discussion_id"]

    expected_session_id = f"{workspace_id}:{discussion_id}"
    assert discussion_agent_client.create_session_calls == [(expected_session_id, workspace_id)]
    assert discussion_agent_client.run_turn_calls[0]["session_id"] == expected_session_id
    assert discussion_agent_client.run_turn_calls[0]["user_id"] == workspace_id


def test_create_discussion_sends_viewport_text_and_document_metadata_in_context(
    client, discussion_agent_client
):
    workspace_id = _create_workspace_with_document(client)

    client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport(), "anchor": _anchor()},
    )

    context = discussion_agent_client.run_turn_calls[0]["context"]
    assert context["viewport_text"] == '<block id="000000">Hello world. Second sentence.</block>'
    assert context["passage_text"] == "Hello world."
    assert context["document_metadata"]["filename"] == "notes.txt"
    assert context["document_blocks"] == [
        {"block_id": "000000", "text": "Hello world. Second sentence."}
    ]


def test_create_discussion_omits_journal_from_context_when_none_exists(client, discussion_agent_client):
    workspace_id = _create_workspace_with_document(client)

    client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    context = discussion_agent_client.run_turn_calls[0]["context"]
    assert "journal" not in context


def test_create_discussion_persists_tool_call_trace(client, discussion_agent_client):
    discussion_agent_client.next_result = AgentTurnResult(
        response_text="Found it.",
        tool_calls=[ToolCallSummary(tool="search_document", input_summary="kant", result_summary="1 match")],
    )
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    tool_calls = response.json()["turns"][0]["tool_calls"]
    assert tool_calls == [{"tool": "search_document", "input_summary": "kant", "result_summary": "1 match"}]


def test_create_discussion_with_unknown_viewport_block_is_rejected(client, discussion_agent_client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={
            "message": "Hi",
            "viewport": {"first_block_id": "999999", "last_block_id": "999999"},
        },
    )

    assert response.status_code == 400
    assert client.get(f"/api/workspaces/{workspace_id}/discussions").json() == []
    assert discussion_agent_client.run_turn_calls == []


def test_create_discussion_with_unknown_anchor_block_is_rejected(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={
            "message": "Hi",
            "viewport": _viewport(),
            "anchor": {
                "first_block_id": "999999",
                "first_block_offset": 0,
                "last_block_id": "999999",
                "last_block_offset": 5,
                "text": "Hello",
            },
        },
    )

    assert response.status_code == 400


def test_create_discussion_without_document_returns_409(client):
    workspace_id = client.post("/api/workspaces").json()["workspace_id"]

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    assert response.status_code == 409


def test_create_discussion_on_missing_workspace_returns_404(client):
    response = client.post(
        "/api/workspaces/does-not-exist/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    assert response.status_code == 404


def test_create_discussion_agent_failure_persists_nothing(client, discussion_agent_client):
    discussion_agent_client.raise_on_run_turn = True
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    assert response.status_code == 502
    assert client.get(f"/api/workspaces/{workspace_id}/discussions").json() == []
    assert client.get(f"/api/workspaces/{workspace_id}").json()["discussion_count"] == 0


def test_create_discussion_session_creation_failure_persists_nothing(client, discussion_agent_client):
    discussion_agent_client.raise_on_create_session = True
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    assert response.status_code == 502
    assert client.get(f"/api/workspaces/{workspace_id}/discussions").json() == []


def test_list_discussions_returns_summaries(client):
    workspace_id = _create_workspace_with_document(client)
    client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "First question?", "viewport": _viewport()},
    )

    response = client.get(f"/api/workspaces/{workspace_id}/discussions")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["turn_count"] == 1
    assert "turns" not in body[0]


def test_get_discussion_returns_full_turns(client):
    workspace_id = _create_workspace_with_document(client)
    discussion_id = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    ).json()["discussion_id"]

    response = client.get(f"/api/workspaces/{workspace_id}/discussions/{discussion_id}")

    assert response.status_code == 200
    assert len(response.json()["turns"]) == 1


def test_get_missing_discussion_returns_404(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.get(f"/api/workspaces/{workspace_id}/discussions/does-not-exist")

    assert response.status_code == 404


def test_post_turn_appends_and_returns_completed_turn(client, discussion_agent_client):
    workspace_id = _create_workspace_with_document(client)
    discussion_id = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    ).json()["discussion_id"]

    discussion_agent_client.next_result = AgentTurnResult(response_text="Second answer.")
    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}/turns",
        json={"message": "Follow-up?", "viewport": _viewport()},
    )

    assert response.status_code == 201
    assert response.json()["agent_response"] == "Second answer."

    detail = client.get(f"/api/workspaces/{workspace_id}/discussions/{discussion_id}").json()
    assert len(detail["turns"]) == 2
    assert detail["turns"][1]["user_message"] == "Follow-up?"


def test_post_turn_reuses_existing_session_without_recreating_it(client, discussion_agent_client):
    workspace_id = _create_workspace_with_document(client)
    discussion_id = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    ).json()["discussion_id"]
    assert len(discussion_agent_client.create_session_calls) == 1

    client.post(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}/turns",
        json={"message": "Follow-up?", "viewport": _viewport()},
    )

    assert len(discussion_agent_client.create_session_calls) == 1


def test_post_turn_on_missing_discussion_returns_404(client):
    workspace_id = _create_workspace_with_document(client)

    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions/does-not-exist/turns",
        json={"message": "Hi", "viewport": _viewport()},
    )

    assert response.status_code == 404


def test_post_turn_agent_failure_persists_nothing(client, discussion_agent_client):
    workspace_id = _create_workspace_with_document(client)
    discussion_id = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    ).json()["discussion_id"]

    discussion_agent_client.raise_on_run_turn = True
    response = client.post(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}/turns",
        json={"message": "Follow-up?", "viewport": _viewport()},
    )

    assert response.status_code == 502
    detail = client.get(f"/api/workspaces/{workspace_id}/discussions/{discussion_id}").json()
    assert len(detail["turns"]) == 1


def test_workspace_discussion_count_reflects_real_discussions(client):
    workspace_id = _create_workspace_with_document(client)
    assert client.get(f"/api/workspaces/{workspace_id}").json()["discussion_count"] == 0

    client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )

    assert client.get(f"/api/workspaces/{workspace_id}").json()["discussion_count"] == 1


def test_discussions_are_isolated_between_workspaces(client):
    workspace_a = _create_workspace_with_document(client)
    workspace_b = _create_workspace_with_document(client)
    discussion_id = client.post(
        f"/api/workspaces/{workspace_a}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    ).json()["discussion_id"]

    assert client.get(f"/api/workspaces/{workspace_b}/discussions").json() == []
    assert (
        client.get(f"/api/workspaces/{workspace_b}/discussions/{discussion_id}").status_code
        == 404
    )
    assert (
        client.post(
            f"/api/workspaces/{workspace_b}/discussions/{discussion_id}/turns",
            json={"message": "hijack", "viewport": _viewport()},
        ).status_code
        == 404
    )


def test_discussion_context_never_leaks_another_workspaces_notes_or_history(
    client, discussion_agent_client
):
    """Security boundary: a new discussion's assembled context (notes,
    discussion_history) must be built only from this workspace's own data —
    never another workspace's, even though both are served by the same
    process/store instance."""
    workspace_a = _create_workspace_with_document(client)
    workspace_b = _create_workspace_with_document(client)

    client.post(
        f"/api/workspaces/{workspace_a}/notes",
        json={"anchor": _anchor(), "text": "SECRET_NOTE_FROM_WORKSPACE_A"},
    )
    client.post(
        f"/api/workspaces/{workspace_a}/discussions",
        json={"message": "SECRET_MESSAGE_FROM_WORKSPACE_A", "viewport": _viewport()},
    )

    client.post(
        f"/api/workspaces/{workspace_b}/discussions",
        json={"message": "Hi from B", "viewport": _viewport(), "anchor": _anchor()},
    )

    context_b = discussion_agent_client.run_turn_calls[-1]["context"]
    assert "SECRET_NOTE_FROM_WORKSPACE_A" not in str(context_b)
    assert "SECRET_MESSAGE_FROM_WORKSPACE_A" not in str(context_b)
    assert context_b.get("notes", []) == []
    assert context_b.get("discussion_history", []) == []


def test_discussion_creation_is_rate_limited_per_workspace(client):
    from app.rate_limit import SlidingWindowRateLimiter

    client.app.state.discussion_creation_limiter = SlidingWindowRateLimiter(
        max_requests=1, window_seconds=60
    )
    workspace_id = _create_workspace_with_document(client)

    first = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    )
    second = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Second discussion", "viewport": _viewport()},
    )

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Retry-After" in second.headers


def test_discussion_turn_is_rate_limited_per_workspace(client):
    from app.rate_limit import SlidingWindowRateLimiter

    workspace_id = _create_workspace_with_document(client)
    discussion_id = client.post(
        f"/api/workspaces/{workspace_id}/discussions",
        json={"message": "Hi", "viewport": _viewport()},
    ).json()["discussion_id"]

    client.app.state.discussion_turn_limiter = SlidingWindowRateLimiter(
        max_requests=1, window_seconds=60
    )
    first = client.post(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}/turns",
        json={"message": "Follow-up 1", "viewport": _viewport()},
    )
    second = client.post(
        f"/api/workspaces/{workspace_id}/discussions/{discussion_id}/turns",
        json={"message": "Follow-up 2", "viewport": _viewport()},
    )

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Retry-After" in second.headers

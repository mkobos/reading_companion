import json

import httpx
import pytest

from app.discussion_agent_client import AgentInvocationError, DiscussionAgentClient


def _client(handler) -> DiscussionAgentClient:
    transport = httpx.MockTransport(handler)
    return DiscussionAgentClient(
        base_url="http://discussion-agent.local", timeout_seconds=5.0, transport=transport
    )


def _ndjson_response(events: list[dict]) -> httpx.Response:
    body = "\n".join(json.dumps(e) for e in events)
    return httpx.Response(200, content=body)


def test_create_session_posts_expected_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"output": {"id": "s1"}})

    client = _client(handler)
    client.create_session(session_id="ws1:d1", user_id="ws1")

    assert captured["url"].endswith("/api/reasoning_engine")
    assert captured["body"] == {
        "class_method": "create_session",
        "input": {"user_id": "ws1", "session_id": "ws1:d1"},
    }


def test_create_session_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client = _client(handler)
    with pytest.raises(AgentInvocationError):
        client.create_session(session_id="ws1:d1", user_id="ws1")


def test_run_turn_sends_json_encoded_envelope_as_message():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ndjson_response(
            [{"content": {"parts": [{"text": "Hello."}]}, "author": "discussion_agent"}]
        )

    client = _client(handler)
    client.run_turn(
        session_id="ws1:d1",
        user_id="ws1",
        user_message="What does this mean?",
        context={"viewport_text": "<block id=\"000000\">Text.</block>", "document_metadata": {}},
    )

    body = captured["body"]
    assert body["class_method"] == "async_stream_query"
    envelope = json.loads(body["input"]["message"])
    assert envelope["user_message"] == "What does this mean?"
    assert envelope["context"]["viewport_text"] == '<block id="000000">Text.</block>'
    assert "<untrusted" not in body["input"]["message"]


def test_run_turn_returns_concatenated_final_text():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response(
            [
                {"content": {"parts": [{"text": "partial"}]}, "partial": True},
                {"content": {"parts": [{"text": "Full answer."}]}},
            ]
        )

    client = _client(handler)
    result = client.run_turn(
        session_id="ws1:d1", user_id="ws1", user_message="Hi", context={}
    )

    assert result.response_text == "Full answer."
    assert result.tool_calls == []


def test_run_turn_summarizes_a_search_document_tool_call():
    # Real wire shape (verified against a live discussion-agent process):
    # search_document's Python function returns {"results": [...]} directly,
    # matching agent-contract.yaml's tool output schema — no ADK auto-wrap
    # involved since the return value is already a dict.
    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response(
            [
                {
                    "content": {
                        "parts": [
                            {"function_call": {"id": "c1", "name": "search_document", "args": {"query": "kant"}}}
                        ]
                    }
                },
                {
                    "content": {
                        "parts": [
                            {
                                "function_response": {
                                    "id": "c1",
                                    "name": "search_document",
                                    "response": {"results": [{"block_id": "000001", "text": "x", "score": 0.9}]},
                                }
                            }
                        ]
                    }
                },
                {"content": {"parts": [{"text": "Answer."}]}},
            ]
        )

    client = _client(handler)
    result = client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})

    assert result.response_text == "Answer."
    assert len(result.tool_calls) == 1
    call = result.tool_calls[0]
    assert call.tool == "search_document"
    assert call.input_summary == "kant"
    assert call.result_summary == "1 match"


def test_run_turn_summarizes_a_search_document_tool_call_with_no_matches():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response(
            [
                {
                    "content": {
                        "parts": [
                            {"function_call": {"id": "c1", "name": "search_document", "args": {"query": "x"}}}
                        ]
                    }
                },
                {
                    "content": {
                        "parts": [
                            {
                                "function_response": {
                                    "id": "c1",
                                    "name": "search_document",
                                    "response": {"results": []},
                                }
                            }
                        ]
                    }
                },
                {"content": {"parts": [{"text": "Answer."}]}},
            ]
        )

    client = _client(handler)
    result = client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})

    assert result.tool_calls[0].result_summary == "0 matches"


def test_run_turn_summarizes_a_web_search_tool_call():
    # Real wire shape: web_search's Python function returns a plain string
    # (already wrapped as untrusted content), which ADK wraps as
    # {"result": "<untrusted ...>...</untrusted>"} — matches
    # agent-contract.yaml's web_search.output.result: {type: string} schema.
    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response(
            [
                {
                    "content": {
                        "parts": [
                            {"function_call": {"id": "c1", "name": "web_search", "args": {"query": "kant"}}}
                        ]
                    }
                },
                {
                    "content": {
                        "parts": [
                            {
                                "function_response": {
                                    "id": "c1",
                                    "name": "web_search",
                                    "response": {"result": '<untrusted source="tool_result">\nSome facts.\n</untrusted>'},
                                }
                            }
                        ]
                    }
                },
                {"content": {"parts": [{"text": "Answer."}]}},
            ]
        )

    client = _client(handler)
    result = client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})

    assert result.tool_calls[0].tool == "web_search"
    assert result.tool_calls[0].result_summary == "1 result"


def test_run_turn_summarizes_a_web_search_tool_call_with_empty_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response(
            [
                {
                    "content": {
                        "parts": [{"function_call": {"id": "c1", "name": "web_search", "args": {"query": "x"}}}]
                    }
                },
                {
                    "content": {
                        "parts": [
                            {"function_response": {"id": "c1", "name": "web_search", "response": {"result": ""}}}
                        ]
                    }
                },
                {"content": {"parts": [{"text": "Answer."}]}},
            ]
        )

    client = _client(handler)
    result = client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})

    assert result.tool_calls[0].result_summary == "0 results"


def test_run_turn_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502)

    client = _client(handler)
    with pytest.raises(AgentInvocationError):
        client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})


def test_run_turn_raises_on_empty_response_text():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response([{"content": {"parts": []}}])

    client = _client(handler)
    with pytest.raises(AgentInvocationError):
        client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})


def test_run_turn_never_retains_raw_tool_result_payload():
    """Security boundary: only a short count-based summary is kept — the raw
    tool_result body (which may itself be untrusted document/web content)
    must never end up in what gets persisted as Turn.tool_calls."""
    sensitive_raw_text = "SENSITIVE_RAW_DOCUMENT_TEXT_THAT_MUST_NOT_BE_PERSISTED"

    def handler(request: httpx.Request) -> httpx.Response:
        return _ndjson_response(
            [
                {
                    "content": {
                        "parts": [
                            {"function_call": {"id": "c1", "name": "search_document", "args": {"query": "q"}}}
                        ]
                    }
                },
                {
                    "content": {
                        "parts": [
                            {
                                "function_response": {
                                    "id": "c1",
                                    "name": "search_document",
                                    "response": {
                                        "results": [
                                            {"block_id": "000001", "text": sensitive_raw_text, "score": 0.9}
                                        ]
                                    },
                                }
                            }
                        ]
                    }
                },
                {"content": {"parts": [{"text": "Answer."}]}},
            ]
        )

    client = _client(handler)
    result = client.run_turn(session_id="ws1:d1", user_id="ws1", user_message="Hi", context={})

    assert result.tool_calls[0].result_summary == "1 match"
    assert sensitive_raw_text not in result.tool_calls[0].result_summary
    assert sensitive_raw_text not in result.response_text


def test_client_applies_the_configured_timeout():
    client = DiscussionAgentClient(base_url="http://discussion-agent.local", timeout_seconds=7.0)

    assert client._client.timeout.read == 7.0
    assert client._client.timeout.connect == 7.0

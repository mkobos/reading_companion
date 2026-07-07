"""HTTP client for discussion-agent's reasoning_engine adapter surface.

Talks to /api/reasoning_engine and /api/stream_reasoning_engine — the same
routes Vertex AI Agent Engine itself forwards calls to (see
discussion-agent/app/app_utils/reasoning_engine_adapter.py) — so this client
keeps working unchanged once the agent is actually deployed to Agent Engine
(only base_url would change).

Per spec/contracts/agent-contract.yaml's discussion_agent.session, the wire
message is a JSON envelope `{"user_message": ..., "context": {...}}`: the
ADK invocation surfaces only accept one message string, so this is decoded
back into a DiscussionContext and wrapped by
discussion-agent/app/agent.py's before_agent_callback. This client never
wraps or escapes untrusted content itself — that responsibility belongs
entirely to discussion-agent.
"""

import json
from dataclasses import dataclass, field

import httpx

_TOOL_NAMES = {"search_document", "web_search"}


class AgentInvocationError(Exception):
    """Raised on any failure to complete a turn: network error, non-2xx
    response, or a stream that never yields response text. Callers must
    treat this as "nothing persisted" per api.openapi.yaml's 502
    AgentFailure response."""


@dataclass(frozen=True)
class ToolCallSummary:
    tool: str
    input_summary: str
    result_summary: str | None = None


@dataclass(frozen=True)
class AgentTurnResult:
    response_text: str
    tool_calls: list[ToolCallSummary] = field(default_factory=list)


class DiscussionAgentClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout_seconds, transport=transport
        )

    def create_session(self, *, session_id: str, user_id: str) -> None:
        try:
            response = self._client.post(
                "/api/reasoning_engine",
                json={
                    "class_method": "create_session",
                    "input": {"user_id": user_id, "session_id": session_id},
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AgentInvocationError(f"Failed to create agent session: {exc}") from exc

    def run_turn(
        self, *, session_id: str, user_id: str, user_message: str, context: dict
    ) -> AgentTurnResult:
        message = json.dumps({"user_message": user_message, "context": context})
        try:
            with self._client.stream(
                "POST",
                "/api/stream_reasoning_engine",
                json={
                    "class_method": "async_stream_query",
                    "input": {"user_id": user_id, "session_id": session_id, "message": message},
                },
            ) as response:
                response.raise_for_status()
                events = [json.loads(line) for line in response.iter_lines() if line.strip()]
        except httpx.HTTPError as exc:
            raise AgentInvocationError(f"Agent turn failed: {exc}") from exc

        return _turn_result_from_events(events)


def _summarize_call_input(args: dict) -> str:
    return str(args.get("query", ""))


def _summarize_call_result(tool: str, response: dict) -> str:
    # search_document returns {"results": [...]} directly (a real dict key,
    # matching agent-contract.yaml exactly). web_search returns a plain
    # string, which ADK auto-wraps as {"result": <value>}
    # (google.adk.flows.llm_flows.functions.__build_response_event, "Specs
    # requires the result to be a dict") — also matching the contract's
    # web_search.output.result: {type: string} schema.
    if tool == "search_document":
        value = response.get("results")
    else:
        value = response.get("result")
    if isinstance(value, list):
        count = len(value)
    elif isinstance(value, str):
        count = 1 if value else 0
    else:
        count = 0
    singular, plural = ("match", "matches") if tool == "search_document" else ("result", "results")
    return f"{count} {singular if count == 1 else plural}"


def _turn_result_from_events(events: list[dict]) -> AgentTurnResult:
    response_text_parts: list[str] = []
    pending_calls: dict[str, ToolCallSummary] = {}
    tool_calls: list[ToolCallSummary] = []

    for event in events:
        if event.get("partial"):
            continue
        for part in (event.get("content") or {}).get("parts") or []:
            if part.get("text"):
                response_text_parts.append(part["text"])

            call = part.get("function_call")
            if call and call.get("name") in _TOOL_NAMES:
                key = call.get("id") or call["name"]
                pending_calls[key] = ToolCallSummary(
                    tool=call["name"], input_summary=_summarize_call_input(call.get("args") or {})
                )

            call_response = part.get("function_response")
            if call_response:
                key = call_response.get("id") or call_response.get("name")
                pending = pending_calls.pop(key, None)
                if pending is not None:
                    tool_calls.append(
                        ToolCallSummary(
                            tool=pending.tool,
                            input_summary=pending.input_summary,
                            result_summary=_summarize_call_result(
                                pending.tool, call_response.get("response") or {}
                            ),
                        )
                    )

    if not response_text_parts:
        raise AgentInvocationError("Agent turn produced no response text.")

    return AgentTurnResult(response_text="".join(response_text_parts), tool_calls=tool_calls)

import type { components } from "../api/types";

type Turn = components["schemas"]["Turn"];

const TOOL_LABELS: Record<NonNullable<Turn["tool_calls"]>[number]["tool"], string> = {
  search_document: "Searched the document",
  web_search: "Searched the web",
};

/** Renders a turn's tool-call trace as plain text lines only — tool
 * summaries are agent-controlled and must never be parsed as HTML. */
export function ToolCallTrace({ toolCalls }: { toolCalls: Turn["tool_calls"] }) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <ul className="space-y-1 text-sm text-gray-600">
      {toolCalls.map((call, index) => (
        <li key={index}>
          {TOOL_LABELS[call.tool]}: {call.input_summary}
          {call.result_summary ? ` — ${call.result_summary}` : ""}
        </li>
      ))}
    </ul>
  );
}

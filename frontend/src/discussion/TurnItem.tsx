import type { components } from "../api/types";
import { ToolCallTrace } from "./ToolCallTrace";

type Turn = components["schemas"]["Turn"];

/** Renders one discussion turn. agent_response is agent-controlled text and
 * must render as plain text only (whitespace-preserved) — never HTML. */
export function TurnItem({ turn }: { turn: Turn }) {
  return (
    <div className="space-y-2 rounded border p-3">
      <p className="font-medium">{turn.user_message}</p>
      <p className="whitespace-pre-wrap">{turn.agent_response}</p>
      <ToolCallTrace toolCalls={turn.tool_calls} />
    </div>
  );
}

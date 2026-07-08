import { memo } from "react";
import type { components } from "../api/types";
import { TurnItem } from "./TurnItem";

type Turn = components["schemas"]["Turn"];

export const TurnList = memo(function TurnList({ turns }: { turns: Turn[] }) {
  return (
    <div className="space-y-3">
      {turns.map((turn) => (
        <TurnItem key={turn.turn_id} turn={turn} />
      ))}
    </div>
  );
});

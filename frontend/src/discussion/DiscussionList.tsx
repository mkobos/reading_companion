import type { components } from "../api/types";

type DiscussionSummary = components["schemas"]["DiscussionSummary"];

interface DiscussionListProps {
  discussions: DiscussionSummary[];
  onSelect: (id: string) => void;
}

export function DiscussionList({ discussions, onSelect }: DiscussionListProps) {
  if (discussions.length === 0) {
    return <p className="text-sm text-gray-500">No discussions yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {discussions.map((discussion) => (
        <li key={discussion.discussion_id}>
          <button
            type="button"
            onClick={() => onSelect(discussion.discussion_id)}
            className="w-full rounded border p-2 text-left"
          >
            <p>{discussion.first_message_preview ?? "New discussion"}</p>
            <p className="text-xs text-gray-500">
              {discussion.turn_count} turn{discussion.turn_count === 1 ? "" : "s"} ·{" "}
              {new Date(discussion.created_at).toLocaleString()}
            </p>
          </button>
        </li>
      ))}
    </ul>
  );
}

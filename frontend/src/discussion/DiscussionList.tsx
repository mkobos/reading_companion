import { useMemo } from "react";
import type { components } from "../api/types";
import { useAnchoredBoxPositions } from "../document/useAnchoredBoxPositions";

type DiscussionSummary = components["schemas"]["DiscussionSummary"];
type Passage = components["schemas"]["Passage"];

interface DiscussionListProps {
  discussions: DiscussionSummary[];
  onSelect: (id: string, anchor: Passage | undefined) => void;
  /** The reading column's DOM node, used to look up each anchored
   * discussion's block and align its box to the same page height. Omitted
   * (or on narrow/mobile viewports, via `md:` classes) falls back to a
   * plain stacked list. */
  readingContainer?: HTMLElement | null;
}

function DiscussionBox({
  discussion,
  onSelect,
}: {
  discussion: DiscussionSummary;
  onSelect: (id: string, anchor: Passage | undefined) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(discussion.discussion_id, discussion.anchor)}
      className="w-full rounded border bg-white p-2 text-left"
    >
      {discussion.anchor && (
        <p
          className="mb-1 truncate text-sm font-medium italic text-gray-700"
          data-testid="discussion-anchor-text"
        >
          &ldquo;{discussion.anchor.text}&rdquo;
        </p>
      )}
      <p>{discussion.first_message_preview ?? "New discussion"}</p>
      <p className="text-xs text-gray-500">
        {discussion.turn_count} turn{discussion.turn_count === 1 ? "" : "s"} ·{" "}
        {new Date(discussion.created_at).toLocaleString()}
      </p>
    </button>
  );
}

export function DiscussionList({ discussions, onSelect, readingContainer }: DiscussionListProps) {
  const unanchored = useMemo(() => discussions.filter((d) => !d.anchor), [discussions]);
  const anchored = useMemo(() => discussions.filter((d) => d.anchor), [discussions]);
  const anchorItems = useMemo(
    () => anchored.map((d) => ({ id: d.discussion_id, blockId: d.anchor!.first_block_id })),
    [anchored],
  );
  const { columnRef, boxRefs, tops, minHeight, ready } = useAnchoredBoxPositions(
    readingContainer ?? null,
    anchorItems,
  );

  if (discussions.length === 0) {
    return <p className="text-sm text-gray-500">No discussions yet.</p>;
  }

  return (
    <div>
      {unanchored.length > 0 && (
        <ul className="space-y-2">
          {unanchored.map((discussion) => (
            <li key={discussion.discussion_id}>
              <DiscussionBox discussion={discussion} onSelect={onSelect} />
            </li>
          ))}
        </ul>
      )}
      {anchored.length > 0 && (
        <div
          ref={columnRef}
          className="mt-2 space-y-2 md:relative md:space-y-0"
          style={{ minHeight: readingContainer ? minHeight : undefined }}
        >
          {anchored.map((discussion) => (
            <div
              key={discussion.discussion_id}
              ref={(el) => {
                boxRefs.current.set(discussion.discussion_id, el);
              }}
              data-testid={`discussion-box-${discussion.discussion_id}`}
              className="md:absolute md:inset-x-0"
              style={{
                top: tops.get(discussion.discussion_id) ?? 0,
                visibility: readingContainer && !ready ? "hidden" : "visible",
              }}
            >
              <DiscussionBox discussion={discussion} onSelect={onSelect} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

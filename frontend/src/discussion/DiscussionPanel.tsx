import { useState } from "react";
import type { components } from "../api/types";
import type { TrackedViewport } from "../document/useViewportTracker";
import { DiscussionListView } from "./DiscussionListView";

type Passage = components["schemas"]["Passage"];

interface DiscussionPanelProps {
  workspaceId: string;
  viewport: TrackedViewport | undefined;
  /** The reading column's DOM node, threaded down to DiscussionListView so
   * anchored discussion boxes can align to their passage's height. */
  readingContainer?: HTMLElement | null;
  /** Notified with a discussion's anchor when its box is clicked (or
   * undefined when leaving the thread/list), so the reading column can
   * highlight the corresponding passage. */
  onHighlightPassage?: (passage: Passage | undefined) => void;
}

export function DiscussionPanel({
  workspaceId,
  viewport,
  readingContainer,
  onHighlightPassage,
}: DiscussionPanelProps) {
  const [activeDiscussionId, setActiveDiscussionId] = useState<string | null>(null);

  return (
    <DiscussionListView
      workspaceId={workspaceId}
      viewport={viewport}
      readingContainer={readingContainer}
      activeDiscussionId={activeDiscussionId}
      onSelectDiscussion={(id, anchor) => {
        setActiveDiscussionId(id);
        onHighlightPassage?.(anchor);
      }}
      onCloseDiscussion={() => {
        setActiveDiscussionId(null);
        onHighlightPassage?.(undefined);
      }}
    />
  );
}

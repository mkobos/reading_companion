import { useState } from "react";
import type { TrackedViewport } from "../document/useViewportTracker";
import { DiscussionListView } from "./DiscussionListView";
import { DiscussionThread } from "./DiscussionThread";

interface DiscussionPanelProps {
  workspaceId: string;
  viewport: TrackedViewport | undefined;
}

export function DiscussionPanel({ workspaceId, viewport }: DiscussionPanelProps) {
  const [activeDiscussionId, setActiveDiscussionId] = useState<string | null>(null);

  return activeDiscussionId === null ? (
    <DiscussionListView
      workspaceId={workspaceId}
      viewport={viewport}
      onDiscussionCreated={setActiveDiscussionId}
    />
  ) : (
    <DiscussionThread
      workspaceId={workspaceId}
      discussionId={activeDiscussionId}
      viewport={viewport}
      onBack={() => setActiveDiscussionId(null)}
    />
  );
}

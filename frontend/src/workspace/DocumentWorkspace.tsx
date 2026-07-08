import { useState } from "react";
import { DiscussionPanel } from "../discussion/DiscussionPanel";
import { ReadingView } from "../document/ReadingView";
import type { TrackedViewport } from "../document/useViewportTracker";

/** Two-column shell for the has_document branch: the reading view on the
 * left, the discussion panel on the right, sharing the tracked viewport
 * (plan §4, Phase 2). */
export function DocumentWorkspace({ workspaceId }: { workspaceId: string }) {
  const [viewport, setViewport] = useState<TrackedViewport | undefined>(undefined);

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <div className="md:w-1/2">
        <ReadingView workspaceId={workspaceId} onViewportChange={setViewport} />
      </div>
      <div className="md:w-1/2">
        <DiscussionPanel workspaceId={workspaceId} viewport={viewport} />
      </div>
    </div>
  );
}

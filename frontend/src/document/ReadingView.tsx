import { useEffect } from "react";
import { useDocument } from "../api/queries";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { Block } from "./Block";
import { useViewportTracker, type TrackedViewport } from "./useViewportTracker";

interface ReadingViewProps {
  workspaceId: string;
  /** Notified with the debounced tracked viewport on every change (Phase 2:
   * threads the visible range into the discussion panel). */
  onViewportChange?: (viewport: TrackedViewport | undefined) => void;
}

/** Renders a workspace's document as an ordered list of blocks and tracks
 * the visible viewport range as the reader scrolls (plan §4). */
export function ReadingView({ workspaceId, onViewportChange }: ReadingViewProps) {
  const { data, isPending, isError, error } = useDocument(workspaceId);
  const { containerRef, viewport } = useViewportTracker();

  useEffect(() => {
    onViewportChange?.(viewport);
  }, [viewport, onViewportChange]);

  if (isPending) return <LoadingState label="Loading document…" />;
  if (isError) {
    return <ErrorNotice message={error instanceof Error ? error.message : "Failed to load document."} />;
  }

  return (
    <div
      ref={containerRef}
      data-testid="reading-view"
      data-first-block-id={viewport?.first_block_id}
      data-last-block-id={viewport?.last_block_id}
      className="mx-auto max-w-2xl space-y-4 p-6"
    >
      {data.blocks.map((block) => (
        <Block key={block.block_id} block={block} />
      ))}
    </div>
  );
}

import { useDocument } from "../api/queries";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { Block } from "./Block";
import { useViewportTracker } from "./useViewportTracker";

/** Renders a workspace's document as an ordered list of blocks and tracks
 * the visible viewport range as the reader scrolls (plan §4). */
export function ReadingView({ workspaceId }: { workspaceId: string }) {
  const { data, isPending, isError, error } = useDocument(workspaceId);
  const { containerRef, viewport } = useViewportTracker();

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

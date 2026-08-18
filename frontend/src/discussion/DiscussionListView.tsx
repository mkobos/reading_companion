import { useCreateDiscussion, useDiscussions } from "../api/queries";
import type { components } from "../api/types";
import type { TrackedViewport } from "../document/useViewportTracker";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { DiscussionList } from "./DiscussionList";
import { DiscussionThread } from "./DiscussionThread";
import { MessageComposer } from "./MessageComposer";

type Passage = components["schemas"]["Passage"];

interface DiscussionListViewProps {
  workspaceId: string;
  viewport: TrackedViewport | undefined;
  /** discussion_id of the discussion currently open, if any. */
  activeDiscussionId?: string | null;
  onSelectDiscussion: (id: string, anchor: Passage | undefined) => void;
  /** Notified when the open discussion (inline or full-view) is closed. */
  onCloseDiscussion: () => void;
  /** The reading column's DOM node, threaded down to DiscussionList so
   * anchored boxes can align to their passage's height (plan §6-7). */
  readingContainer?: HTMLElement | null;
}

export function DiscussionListView({
  workspaceId,
  viewport,
  activeDiscussionId,
  onSelectDiscussion,
  onCloseDiscussion,
  readingContainer,
}: DiscussionListViewProps) {
  const { data, isPending, isError, error } = useDiscussions(workspaceId);
  const createDiscussion = useCreateDiscussion(workspaceId);

  // Anchored discussions unfold in place at their box's page-aligned
  // position (Google-Docs style). Unanchored discussions — and one just
  // created via the composer below, before the list has refetched it —
  // have no box to unfold at, so they fall back to a full-view thread.
  const activeDiscussion = data?.find((d) => d.discussion_id === activeDiscussionId);
  const expandInline = activeDiscussionId != null && activeDiscussion?.anchor != null;

  if (activeDiscussionId != null && !expandInline) {
    return (
      <DiscussionThread
        workspaceId={workspaceId}
        discussionId={activeDiscussionId}
        viewport={viewport}
        onBack={onCloseDiscussion}
      />
    );
  }

  return (
    <div className="space-y-3">
      {/* Rendered above the discussion list/canvas (rather than below, as
          before) so it stays reachable right under the tab bar even once
          the anchored-box canvas below grows as tall as the document. */}
      <MessageComposer
        viewport={viewport}
        placeholder="Ask about this document..."
        onSend={(message) =>
          createDiscussion
            .mutateAsync({ message, viewport: viewport! })
            .then((discussion) => {
              onSelectDiscussion(discussion.discussion_id, undefined);
              return discussion;
            })
        }
      />
      {isPending && <LoadingState label="Loading discussions…" />}
      {isError && (
        <ErrorNotice message={error instanceof Error ? error.message : "Failed to load discussions."} />
      )}
      {data && (
        <DiscussionList
          discussions={data}
          onSelect={onSelectDiscussion}
          readingContainer={readingContainer}
          expandedId={expandInline ? activeDiscussionId : null}
          renderExpanded={(id) => (
            <DiscussionThread
              workspaceId={workspaceId}
              discussionId={id}
              viewport={viewport}
              onBack={onCloseDiscussion}
            />
          )}
        />
      )}
    </div>
  );
}

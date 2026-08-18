import { useCreateDiscussion, useDiscussions } from "../api/queries";
import type { components } from "../api/types";
import type { TrackedViewport } from "../document/useViewportTracker";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { DiscussionList } from "./DiscussionList";
import { MessageComposer } from "./MessageComposer";

type Passage = components["schemas"]["Passage"];

interface DiscussionListViewProps {
  workspaceId: string;
  viewport: TrackedViewport | undefined;
  onSelectDiscussion: (id: string, anchor: Passage | undefined) => void;
  /** The reading column's DOM node, threaded down to DiscussionList so
   * anchored boxes can align to their passage's height (plan §6-7). */
  readingContainer?: HTMLElement | null;
}

export function DiscussionListView({
  workspaceId,
  viewport,
  onSelectDiscussion,
  readingContainer,
}: DiscussionListViewProps) {
  const { data, isPending, isError, error } = useDiscussions(workspaceId);
  const createDiscussion = useCreateDiscussion(workspaceId);

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
        <DiscussionList discussions={data} onSelect={onSelectDiscussion} readingContainer={readingContainer} />
      )}
    </div>
  );
}

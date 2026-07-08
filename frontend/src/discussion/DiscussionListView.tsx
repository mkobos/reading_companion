import { useCreateDiscussion, useDiscussions } from "../api/queries";
import type { TrackedViewport } from "../document/useViewportTracker";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { DiscussionList } from "./DiscussionList";
import { MessageComposer } from "./MessageComposer";

interface DiscussionListViewProps {
  workspaceId: string;
  viewport: TrackedViewport | undefined;
  onDiscussionCreated: (id: string) => void;
}

export function DiscussionListView({ workspaceId, viewport, onDiscussionCreated }: DiscussionListViewProps) {
  const { data, isPending, isError, error } = useDiscussions(workspaceId);
  const createDiscussion = useCreateDiscussion(workspaceId);

  return (
    <div className="space-y-3">
      {isPending && <LoadingState label="Loading discussions…" />}
      {isError && (
        <ErrorNotice message={error instanceof Error ? error.message : "Failed to load discussions."} />
      )}
      {data && <DiscussionList discussions={data} onSelect={onDiscussionCreated} />}
      <MessageComposer
        viewport={viewport}
        placeholder="Ask about this document..."
        onSend={(message) =>
          createDiscussion
            .mutateAsync({ message, viewport: viewport! })
            .then((discussion) => {
              onDiscussionCreated(discussion.discussion_id);
              return discussion;
            })
        }
      />
    </div>
  );
}

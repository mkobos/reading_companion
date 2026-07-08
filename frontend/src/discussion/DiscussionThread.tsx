import { useDiscussion, usePostTurn } from "../api/queries";
import type { TrackedViewport } from "../document/useViewportTracker";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { MessageComposer } from "./MessageComposer";
import { TurnList } from "./TurnList";

interface DiscussionThreadProps {
  workspaceId: string;
  discussionId: string;
  viewport: TrackedViewport | undefined;
  onBack: () => void;
}

export function DiscussionThread({ workspaceId, discussionId, viewport, onBack }: DiscussionThreadProps) {
  const { data, isPending, isError, error } = useDiscussion(workspaceId, discussionId);
  const postTurn = usePostTurn(workspaceId, discussionId);

  return (
    <div className="space-y-3">
      <button type="button" onClick={onBack} className="text-sm underline">
        Back to discussions
      </button>

      {isPending && <LoadingState label="Loading discussion…" />}
      {isError && (
        <ErrorNotice message={error instanceof Error ? error.message : "Failed to load discussion."} />
      )}
      {data && (
        <>
          <TurnList turns={data.turns} />
          <MessageComposer
            viewport={viewport}
            onSend={(message) => postTurn.mutateAsync({ message, viewport: viewport! })}
          />
        </>
      )}
    </div>
  );
}

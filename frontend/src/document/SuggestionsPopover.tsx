import { useEffect, useRef, useState } from "react";
import { useCreateDiscussion, useSuggestions } from "../api/queries";
import type { components } from "../api/types";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { mapSuggestionsError } from "./mapSuggestionsError";
import type { TrackedViewport } from "./useViewportTracker";

type Passage = components["schemas"]["Passage"];

interface SuggestionsPopoverProps {
  workspaceId: string;
  passage: Passage;
  viewport: TrackedViewport | undefined;
  onDismiss: () => void;
  /** Called after a suggestion (or the free-form fallback) successfully
   * starts a discussion, so the parent can switch to the Discussions tab. */
  onDiscussionStarted?: () => void;
}

/** Ephemeral floating popover shown when a passage is marked: fetches
 * suggested questions (at most once per mark) and lets the user start a
 * discussion from one of them, or type a free-form question if suggestions
 * are unavailable. Dismissing it persists nothing — no note, no
 * discussion, no mark record. */
export function SuggestionsPopover({
  workspaceId,
  passage,
  viewport,
  onDismiss,
  onDiscussionStarted,
}: SuggestionsPopoverProps) {
  const suggestions = useSuggestions(workspaceId);
  const createDiscussion = useCreateDiscussion(workspaceId);
  const [error, setError] = useState<string | undefined>(undefined);
  const [fallbackText, setFallbackText] = useState("");
  const requestedFor = useRef<Passage | undefined>(undefined);

  useEffect(() => {
    if (viewport === undefined) return;
    if (requestedFor.current === passage) return;
    requestedFor.current = passage;
    setError(undefined);
    suggestions.mutate(
      { anchor: passage, viewport },
      { onError: (err) => setError(mapSuggestionsError(err)) },
    );
    // Only re-fires when the mark itself changes, per the "at most one
    // side-effect-free call per mark" security assertion.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passage, viewport]);

  const startDiscussion = (message: string) => {
    if (!viewport || message.trim().length === 0) return;
    createDiscussion.mutate(
      { message, viewport, anchor: passage },
      {
        onSuccess: () => {
          onDismiss();
          onDiscussionStarted?.();
        },
        onError: (err) => setError(mapSuggestionsError(err)),
      },
    );
  };

  return (
    <div role="dialog" aria-label="Passage suggestions" className="space-y-2 rounded border bg-white p-3 shadow">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium">&ldquo;{passage.text}&rdquo;</p>
        <button type="button" aria-label="Dismiss" onClick={onDismiss} className="opacity-70">
          ×
        </button>
      </div>

      {suggestions.isPending && <LoadingState label="Getting suggestions…" />}
      {error && <ErrorNotice message={error} />}

      {suggestions.isSuccess && (
        <ul className="space-y-1">
          {suggestions.data.suggestions.map((s) => (
            <li key={s}>
              <button type="button" onClick={() => startDiscussion(s)} className="text-left text-sm underline">
                {s}
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            startDiscussion(fallbackText);
          }}
          className="space-y-1"
        >
          <textarea
            value={fallbackText}
            onChange={(event) => setFallbackText(event.target.value)}
            placeholder="Ask your own question about this passage"
            className="w-full rounded border p-2"
            rows={2}
          />
          <button type="submit" className="rounded border px-2 py-1 text-sm">
            Ask
          </button>
        </form>
      )}
    </div>
  );
}

import { useState } from "react";
import type { TrackedViewport } from "../document/useViewportTracker";
import { ErrorNotice } from "../ui/ErrorNotice";
import { mapComposerError } from "./mapComposerError";
import { PendingIndicator } from "./PendingIndicator";

interface MessageComposerProps {
  onSend: (message: string) => Promise<unknown>;
  viewport: TrackedViewport | undefined;
  placeholder?: string;
}

/** Text composer for a discussion turn. Synchronous request/response (5-30s
 * per turn, no streaming): submit disables the input and shows a pending
 * indicator, clears the input only on success, and on failure retains the
 * input with a Resend button so the same message can be resubmitted. */
export function MessageComposer({ onSend, viewport, placeholder }: MessageComposerProps) {
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  const canSend = viewport !== undefined && input.trim().length > 0 && !submitting;

  const submit = async () => {
    setSubmitting(true);
    try {
      await onSend(input);
      setInput("");
      setError(undefined);
    } catch (err) {
      setError(mapComposerError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSend) return;
    void submit();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <textarea
        value={input}
        onChange={(event) => setInput(event.target.value)}
        disabled={submitting}
        placeholder={placeholder}
        className="w-full rounded border p-2"
        rows={3}
      />
      {submitting && <PendingIndicator />}
      {error && (
        <div className="space-y-2">
          <ErrorNotice message={error} />
          <button
            type="button"
            onClick={() => void submit()}
            className="rounded border px-3 py-1 text-sm"
          >
            Resend
          </button>
        </div>
      )}
      <button type="submit" disabled={!canSend} className="rounded border px-3 py-1 text-sm">
        Send
      </button>
    </form>
  );
}

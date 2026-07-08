import { useState } from "react";
import { ErrorNotice } from "../ui/ErrorNotice";
import { mapNoteError } from "./mapNoteError";

const EMPTY_TEXT_MESSAGE = "Note text can't be empty.";

interface NoteComposerProps {
  initialText?: string;
  saveLabel?: string;
  onSave: (text: string) => Promise<unknown>;
  onCancel: () => void;
}

/** Text composer for creating or editing a note. Rejects empty/whitespace
 * text client-side (UX only; the backend's Field(min_length=1) 422 is the
 * real boundary) before any network call, keeping the composer open with a
 * validation message. On a save failure the composer stays open with the
 * typed text retained, mirroring MessageComposer's resend-friendly pattern. */
export function NoteComposer({ initialText = "", saveLabel = "Save", onSave, onCancel }: NoteComposerProps) {
  const [text, setText] = useState(initialText);
  const [submitting, setSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);

  const submit = async () => {
    if (text.trim().length === 0) {
      setValidationError(EMPTY_TEXT_MESSAGE);
      return;
    }
    setValidationError(undefined);
    setError(undefined);
    setSubmitting(true);
    try {
      await onSave(text);
    } catch (err) {
      setError(mapNoteError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
      className="space-y-2"
    >
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        disabled={submitting}
        className="w-full rounded border p-2"
        rows={3}
      />
      {validationError && <ErrorNotice message={validationError} />}
      {error && <ErrorNotice message={error} />}
      <div className="flex gap-2">
        <button type="submit" disabled={submitting} className="rounded border px-3 py-1 text-sm">
          {saveLabel}
        </button>
        <button type="button" onClick={onCancel} className="rounded border px-3 py-1 text-sm">
          Cancel
        </button>
      </div>
    </form>
  );
}

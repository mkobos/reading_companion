import type { components } from "../api/types";

type Note = components["schemas"]["Note"];

interface NoteIndicatorProps {
  note: Note;
  onSelect: (noteId: string) => void;
}

/** Small inline marker anchored in the reading column for an existing note.
 * Renders no note content itself (that's NoteItem, in the Notes tab) — just
 * a click target that surfaces the note. */
export function NoteIndicator({ note, onSelect }: NoteIndicatorProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(note.note_id)}
      aria-label={`Note: ${note.text}`}
      data-testid={`note-indicator-${note.note_id}`}
      className="ml-1 rounded border px-1 text-xs align-super"
    >
      📝
    </button>
  );
}

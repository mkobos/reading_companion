import { useCreateNote, useDeleteNote, useNotes, useUpdateNote } from "../api/queries";
import type { components } from "../api/types";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { NoteComposer } from "./NoteComposer";
import { NoteItem } from "./NoteItem";

type Passage = components["schemas"]["Passage"];

interface NotesTabProps {
  workspaceId: string;
  /** The currently marked (ephemeral) passage, if any — used as the anchor
   * for a new note. Lifted from DocumentWorkspace, mirroring the shared
   * viewport state pattern. */
  markedPassage?: Passage;
  /** Called after the marked-passage composer is saved or cancelled, so the
   * parent can clear the mark (no persisted footprint from a dismissal). */
  onMarkHandled?: () => void;
}

/** Full CRUD UI for notes: a composer anchored to the currently marked
 * passage (if any) plus the list of existing notes with inline edit/delete. */
export function NotesTab({ workspaceId, markedPassage, onMarkHandled }: NotesTabProps) {
  const { data, isPending, isError, error } = useNotes(workspaceId);
  const createNote = useCreateNote(workspaceId);
  const updateNote = useUpdateNote(workspaceId);
  const deleteNote = useDeleteNote(workspaceId);

  return (
    <div className="space-y-3">
      {markedPassage ? (
        <div className="space-y-1">
          <p className="text-xs text-gray-500">New note on: &ldquo;{markedPassage.text}&rdquo;</p>
          <NoteComposer
            saveLabel="Add note"
            onSave={(text) =>
              createNote.mutateAsync({ anchor: markedPassage, text }).then(() => onMarkHandled?.())
            }
            onCancel={() => onMarkHandled?.()}
          />
        </div>
      ) : (
        <p className="text-sm text-gray-500">Select text in the document to add a note.</p>
      )}

      {isPending && <LoadingState label="Loading notes…" />}
      {isError && (
        <ErrorNotice message={error instanceof Error ? error.message : "Failed to load notes."} />
      )}
      {data && data.length === 0 && <p className="text-sm text-gray-500">No notes yet.</p>}
      {data &&
        data.map((note) => (
          <NoteItem
            key={note.note_id}
            note={note}
            onUpdate={(text) => updateNote.mutateAsync({ noteId: note.note_id, text })}
            onDelete={() => deleteNote.mutateAsync(note.note_id)}
          />
        ))}
    </div>
  );
}

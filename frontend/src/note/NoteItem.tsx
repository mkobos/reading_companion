import { useState } from "react";
import type { components } from "../api/types";
import { ConfirmDialog } from "../ui/ConfirmDialog";
import { NoteComposer } from "./NoteComposer";

type Note = components["schemas"]["Note"];

interface NoteItemProps {
  note: Note;
  onUpdate: (text: string) => Promise<unknown>;
  onDelete: () => Promise<unknown>;
}

/** One note in the Notes tab list: view, inline edit (via NoteComposer), and
 * delete (behind a ConfirmDialog, per Phase 1's ConfirmDialog convention). */
export function NoteItem({ note, onUpdate, onDelete }: NoteItemProps) {
  const [editing, setEditing] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  if (editing) {
    return (
      <NoteComposer
        initialText={note.text}
        saveLabel="Save"
        onSave={(text) => onUpdate(text).then(() => setEditing(false))}
        onCancel={() => setEditing(false)}
      />
    );
  }

  return (
    <div className="space-y-1 rounded border p-2">
      <p className="text-xs text-gray-500">&ldquo;{note.anchor.text}&rdquo;</p>
      <p>{note.text}</p>
      <div className="flex gap-2">
        <button type="button" onClick={() => setEditing(true)} className="text-sm underline">
          Edit
        </button>
        <button
          type="button"
          onClick={() => setConfirmingDelete(true)}
          className="text-sm text-red-600 underline"
        >
          Delete
        </button>
      </div>
      {confirmingDelete && (
        <ConfirmDialog
          title="Delete note"
          message="Delete this note? This can't be undone."
          confirmLabel="Delete"
          onConfirm={() => {
            setConfirmingDelete(false);
            void onDelete();
          }}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </div>
  );
}

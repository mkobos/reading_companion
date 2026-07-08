import { ApiError } from "../lib/errors";

const GENERIC_MESSAGE = "Couldn't save that note.";
const ANCHOR_MESSAGE = "Couldn't anchor that selection. Try selecting the passage again.";

/** Maps a note create/update/delete failure into display text. Never
 * surfaces a raw exception's message/stack — only ApiError bodies or this
 * module's own fixed copy. A 400 (invalid passage anchor) is always mapped
 * to a fixed message, never echoing the backend's (already generic) text,
 * per the passage-anchor-tampering security boundary. */
export function mapNoteError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 400) {
      return ANCHOR_MESSAGE;
    }
    return err.message || GENERIC_MESSAGE;
  }
  return GENERIC_MESSAGE;
}

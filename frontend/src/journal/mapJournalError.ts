import { ApiError } from "../lib/errors";

const GENERIC_MESSAGE = "Couldn't generate the journal.";
const NOTHING_TO_SYNTHESIZE_MESSAGE = "Nothing to reflect on yet — add some notes or discussions first.";
const UNAVAILABLE_MESSAGE =
  "Journal generation is currently unavailable; your previous journal, if any, is unchanged.";

/** Maps a journal-generation failure into display text. Never surfaces a
 * raw exception's message/stack — only ApiError bodies or this module's own
 * fixed copy. Regeneration is strictly user-button-driven; this mapper
 * never triggers an automatic retry. */
export function mapJournalError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 409) {
      return NOTHING_TO_SYNTHESIZE_MESSAGE;
    }
    if (err.status === 429) {
      const base = err.message || GENERIC_MESSAGE;
      return err.retryAfterSeconds !== undefined ? `${base} Try again in ${err.retryAfterSeconds}s.` : base;
    }
    if (err.status === 503) {
      return err.message || UNAVAILABLE_MESSAGE;
    }
    return err.message || GENERIC_MESSAGE;
  }
  return GENERIC_MESSAGE;
}

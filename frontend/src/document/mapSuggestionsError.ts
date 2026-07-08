import { ApiError } from "../lib/errors";

const GENERIC_MESSAGE = "Couldn't get suggestions for that passage.";
const ANCHOR_MESSAGE = "Couldn't anchor that selection. Try selecting the passage again.";
const UNAVAILABLE_MESSAGE = "Suggestions are currently unavailable. Ask your own question below.";

/** Maps a suggestions-request failure into display text. Never surfaces a
 * raw exception's message/stack — only ApiError bodies or this module's own
 * fixed copy. A 400 (invalid passage anchor) is always mapped to a fixed
 * message, never echoing the backend's (already generic) text. */
export function mapSuggestionsError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 400) {
      return ANCHOR_MESSAGE;
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

import { ApiError } from "../lib/errors";

const CONNECTION_LOST_MESSAGE =
  "Connection lost before the agent responded. Your message is still here — resend it.";

/** Maps a send-failure into display text. Never surfaces a raw network
 * exception's message/stack — only ApiError bodies (already backend
 * user-facing text) or this module's own fixed copy. */
export function mapComposerError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 429) {
      return err.retryAfterSeconds !== undefined
        ? `${err.message} Try again in ${err.retryAfterSeconds}s.`
        : err.message;
    }
    return err.message;
  }
  return CONNECTION_LOST_MESSAGE;
}

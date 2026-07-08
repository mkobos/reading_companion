/** Typed error thrown by the API client for any non-2xx response, parsed
 * from the backend's uniform `Error{message}` body and (for 429s) the
 * `Retry-After` header. */
export class ApiError extends Error {
  readonly status: number;
  readonly retryAfterSeconds?: number;

  constructor(status: number, message: string, retryAfterSeconds?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

/** TanStack Query retry predicate for reads: client errors (4xx, incl. 404
 * "not found" and 429 "rate limited") are terminal and retrying them is
 * both pointless and, for 429, actively harmful (retry-storm risk per plan
 * §6.6) — only retry on transient failures (5xx/network). */
export function shouldRetryRead(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < 3;
}

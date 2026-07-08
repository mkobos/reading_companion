import { ApiError } from "../lib/errors";

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "/api";

export interface RequestOptions extends Omit<RequestInit, "body"> {
  /** JSON-serializable body; sets Content-Type: application/json. */
  json?: unknown;
  /** Pass a FormData/Blob/etc. body directly (e.g. multipart upload). */
  body?: BodyInit;
}

/** Thin typed fetch wrapper. Prepends the API base URL, encodes/decodes
 * JSON, and maps any non-2xx response to a typed ApiError parsed from the
 * uniform `Error{message}` body and the `Retry-After` header. Never
 * retries automatically — retry policy belongs to the caller (TanStack
 * Query hooks), not this layer. */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { json, headers, body, ...rest } = options;
  const init: RequestInit = { ...rest, headers: { ...headers } };

  if (json !== undefined) {
    init.body = JSON.stringify(json);
    init.headers = { "Content-Type": "application/json", ...init.headers };
  } else if (body !== undefined) {
    init.body = body;
  }

  const response = await fetch(`${BASE_URL}${path}`, init);

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    let message = response.statusText || `Request failed with status ${response.status}`;
    try {
      const errorBody: unknown = await response.json();
      if (
        errorBody &&
        typeof errorBody === "object" &&
        "message" in errorBody &&
        typeof (errorBody as { message: unknown }).message === "string"
      ) {
        message = (errorBody as { message: string }).message;
      }
    } catch {
      // Body wasn't JSON; fall back to the status text already set above.
    }

    const retryAfterHeader = response.headers.get("Retry-After");
    const retryAfterSeconds =
      retryAfterHeader !== null && Number.isFinite(Number(retryAfterHeader))
        ? Number(retryAfterHeader)
        : undefined;

    throw new ApiError(response.status, message, retryAfterSeconds);
  }

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

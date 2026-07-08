import { describe, expect, it } from "vitest";
import { ApiError } from "../../src/lib/errors";

describe("ApiError", () => {
  it("carries status, message, and an optional retryAfterSeconds", () => {
    const err = new ApiError(429, "Too many requests", 30);
    expect(err).toBeInstanceOf(Error);
    expect(err.status).toBe(429);
    expect(err.message).toBe("Too many requests");
    expect(err.retryAfterSeconds).toBe(30);
  });

  it("defaults retryAfterSeconds to undefined when not provided", () => {
    const err = new ApiError(404, "Not found");
    expect(err.retryAfterSeconds).toBeUndefined();
  });
});

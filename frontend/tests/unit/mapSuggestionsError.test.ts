import { describe, expect, it } from "vitest";
import { ApiError } from "../../src/lib/errors";
import { mapSuggestionsError } from "../../src/document/mapSuggestionsError";

describe("mapSuggestionsError", () => {
  it("maps a 400 (invalid anchor) to a generic re-selection message, never echoing server text", () => {
    const msg = mapSuggestionsError(new ApiError(400, "Passage anchor references an unknown block."));
    expect(msg).toMatch(/select/i);
    expect(msg).not.toMatch(/unknown block/i);
  });

  it("includes retryAfterSeconds in the 429 message", () => {
    const msg = mapSuggestionsError(new ApiError(429, "Rate limited", 7));
    expect(msg).toMatch(/7s/);
  });

  it("falls back to a sensible non-empty string for a 503 with no JSON body (empty message)", () => {
    const msg = mapSuggestionsError(new ApiError(503, ""));
    expect(typeof msg).toBe("string");
    expect(msg.length).toBeGreaterThan(0);
  });

  it("returns a fixed generic string for a non-ApiError", () => {
    expect(mapSuggestionsError(new Error("boom"))).toBe("Couldn't get suggestions for that passage.");
  });
});

import { describe, expect, it } from "vitest";
import { ApiError } from "../../src/lib/errors";
import { mapJournalError } from "../../src/journal/mapJournalError";

describe("mapJournalError", () => {
  it("maps a 409 to a 'nothing to reflect on yet' message", () => {
    expect(mapJournalError(new ApiError(409, ""))).toMatch(/nothing to reflect/i);
  });

  it("includes retryAfterSeconds in the 429 message", () => {
    expect(mapJournalError(new ApiError(429, "Rate limited", 12))).toMatch(/12s/);
  });

  it("falls back to a sensible non-empty string for a 503 with no JSON body (empty message)", () => {
    const msg = mapJournalError(new ApiError(503, ""));
    expect(typeof msg).toBe("string");
    expect(msg.length).toBeGreaterThan(0);
  });

  it("returns a fixed generic string for a non-ApiError", () => {
    expect(mapJournalError(new Error("boom"))).toBe("Couldn't generate the journal.");
  });
});

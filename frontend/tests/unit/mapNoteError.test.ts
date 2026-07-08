import { describe, expect, it } from "vitest";
import { ApiError } from "../../src/lib/errors";
import { mapNoteError } from "../../src/note/mapNoteError";

describe("mapNoteError", () => {
  it("maps a 400 (invalid anchor) to a generic re-selection message, never echoing server text", () => {
    const msg = mapNoteError(new ApiError(400, "Passage anchor references an unknown block."));
    expect(msg).toMatch(/select/i);
    expect(msg).not.toMatch(/unknown block/i);
  });

  it("falls back to a sensible non-empty string for a response with no JSON body (empty message)", () => {
    const msg = mapNoteError(new ApiError(500, ""));
    expect(typeof msg).toBe("string");
    expect(msg.length).toBeGreaterThan(0);
  });

  it("returns a fixed generic string for a non-ApiError (never a raw exception message)", () => {
    expect(mapNoteError(new Error("boom"))).toBe("Couldn't save that note.");
  });
});

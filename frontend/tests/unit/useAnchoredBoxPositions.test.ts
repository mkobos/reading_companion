import { describe, expect, it } from "vitest";
import { resolveCollisions } from "../../src/document/useAnchoredBoxPositions";

describe("resolveCollisions", () => {
  it("leaves well-separated boxes at their raw top", () => {
    const result = resolveCollisions([
      { id: "a", top: 0, height: 40 },
      { id: "b", top: 200, height: 40 },
    ]);
    expect(result.get("a")).toBe(0);
    expect(result.get("b")).toBe(200);
  });

  it("pushes an overlapping box down just enough to clear the one above it", () => {
    const result = resolveCollisions([
      { id: "a", top: 0, height: 60 },
      { id: "b", top: 20, height: 40 }, // would overlap [0,60)
    ]);
    expect(result.get("a")).toBe(0);
    expect(result.get("b")).toBe(68); // 0 + 60 + GAP(8)
  });

  it("cascades the push through three overlapping boxes in a row", () => {
    const result = resolveCollisions([
      { id: "a", top: 0, height: 50 },
      { id: "b", top: 10, height: 50 },
      { id: "c", top: 20, height: 50 },
    ]);
    expect(result.get("a")).toBe(0);
    expect(result.get("b")).toBe(58); // 0 + 50 + 8
    expect(result.get("c")).toBe(116); // 58 + 50 + 8
  });

  it("clamps a negative raw top (anchor above the column's own top edge) to zero", () => {
    const result = resolveCollisions([{ id: "a", top: -30, height: 40 }]);
    expect(result.get("a")).toBe(0);
  });

  it("resolves out-of-order input by raw top, independent of array order", () => {
    const result = resolveCollisions([
      { id: "later", top: 200, height: 40 },
      { id: "earlier", top: 0, height: 40 },
    ]);
    expect(result.get("earlier")).toBe(0);
    expect(result.get("later")).toBe(200);
  });
});

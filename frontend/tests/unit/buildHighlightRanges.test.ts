import { describe, expect, it } from "vitest";
import { buildHighlightRanges } from "../../src/document/buildHighlightRanges";

const BLOCKS = [
  { block_id: "000000", text: "First paragraph." },
  { block_id: "000001", text: "Second paragraph here." },
  { block_id: "000002", text: "Third one." },
  { block_id: "000003", text: "Fourth one." },
];

describe("buildHighlightRanges", () => {
  it("returns a single range for a single-block passage", () => {
    const passage = {
      first_block_id: "000001",
      first_block_offset: 0,
      last_block_id: "000001",
      last_block_offset: 6,
      text: "Second",
    };
    const ranges = buildHighlightRanges(passage, BLOCKS);
    expect(ranges).toEqual(new Map([["000001", { start: 0, end: 6 }]]));
  });

  it("covers first-block-suffix, whole intervening blocks, and last-block-prefix for a multi-block passage", () => {
    const passage = {
      first_block_id: "000000",
      first_block_offset: 6,
      last_block_id: "000003",
      last_block_offset: 6,
      text: "paragraph.\nSecond paragraph here.\nThird one.\nFourth",
    };
    const ranges = buildHighlightRanges(passage, BLOCKS);
    expect(ranges).toEqual(
      new Map([
        ["000000", { start: 6, end: 16 }],
        ["000001", { start: 0, end: 22 }],
        ["000002", { start: 0, end: 10 }],
        ["000003", { start: 0, end: 6 }],
      ]),
    );
  });

  it("handles code-point lengths correctly for blocks containing surrogate-pair characters", () => {
    const blocks = [
      { block_id: "000000", text: "a😀b" },
      { block_id: "000001", text: "c😀d" },
    ];
    const passage = {
      first_block_id: "000000",
      first_block_offset: 1,
      last_block_id: "000001",
      last_block_offset: 2,
      text: "😀b\nc😀",
    };
    const ranges = buildHighlightRanges(passage, blocks);
    expect(ranges).toEqual(
      new Map([
        ["000000", { start: 1, end: 3 }],
        ["000001", { start: 0, end: 2 }],
      ]),
    );
  });
});

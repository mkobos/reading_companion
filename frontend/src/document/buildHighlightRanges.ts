import type { components } from "../api/types";
import { codePointLength } from "./textOffsets";

type Passage = components["schemas"]["Passage"];

/** Minimal shape needed from a document block to compute per-block
 * highlight ranges — see SelectionBlock in passageFromSelection.ts for the
 * matching "authoritative text" convention. */
export interface HighlightableBlock {
  block_id: string;
  text: string;
}

/** Given a Passage and the document's ordered blocks, returns the
 * code-point range within each covered block that should be rendered
 * highlighted: the first block's suffix from `first_block_offset`, any
 * intervening blocks in full, and the last block's prefix up to
 * `last_block_offset`. A single-block passage returns one entry. */
export function buildHighlightRanges(
  passage: Passage,
  blocks: HighlightableBlock[],
): Map<string, { start: number; end: number }> {
  const ranges = new Map<string, { start: number; end: number }>();

  if (passage.first_block_id === passage.last_block_id) {
    ranges.set(passage.first_block_id, {
      start: passage.first_block_offset,
      end: passage.last_block_offset,
    });
    return ranges;
  }

  const orderedIds = blocks.map((b) => b.block_id);
  const startIndex = orderedIds.indexOf(passage.first_block_id);
  const endIndex = orderedIds.indexOf(passage.last_block_id);
  if (startIndex === -1 || endIndex === -1) return ranges;

  const firstBlock = blocks[startIndex]!;
  ranges.set(passage.first_block_id, {
    start: passage.first_block_offset,
    end: codePointLength(firstBlock.text),
  });

  for (let i = startIndex + 1; i < endIndex; i++) {
    const block = blocks[i]!;
    ranges.set(block.block_id, { start: 0, end: codePointLength(block.text) });
  }

  ranges.set(passage.last_block_id, { start: 0, end: passage.last_block_offset });
  return ranges;
}

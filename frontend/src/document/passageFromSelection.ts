import type { components } from "../api/types";

type Passage = components["schemas"]["Passage"];

/** Minimal shape needed from a document block: the authoritative text used
 * to derive a passage's `text` field. NEVER trust Selection.toString() for
 * this — always look the block text up from React state by block_id. */
export interface SelectionBlock {
  block_id: string;
  text: string;
}

const JOIN = "\n";

function findBlockElement(node: Node | null): HTMLElement | null {
  if (!node) return null;
  const el = node.nodeType === Node.ELEMENT_NODE ? (node as Element) : node.parentElement;
  return (el?.closest("[data-block-id]") as HTMLElement | null) ?? null;
}

/** Counts Text nodes anywhere in `el`'s subtree. passageFromSelection
 * assumes exactly one per block (Block.tsx renders `{block.text}` as a
 * single child, even for code_block's nested <pre><code> structure) so DOM
 * UTF-16 offsets can be mapped 1:1 onto the block's authoritative text. */
function countTextNodes(el: Element): number {
  let count = 0;
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) count += 1;
  return count;
}

/** Converts a UTF-16 string offset (as reported by DOM Range) to a Unicode
 * code-point offset (as used by Block.text/Passage offsets, matching
 * Python's code-point-based string indexing on the backend). */
function codePointIndex(str: string, utf16Offset: number): number {
  return Array.from(str.slice(0, utf16Offset)).length;
}

/** Code-point-safe slice — NOT the same as String.prototype.slice, which is
 * UTF-16-indexed and would split surrogate pairs. */
function codePointSlice(str: string, from: number, to?: number): string {
  return Array.from(str).slice(from, to).join("");
}

/** Derives a Passage from the current window Selection, or undefined if the
 * selection is empty/collapsed/outside any block/spans a block with more
 * than one text node. Mirrors backend/app/passages.py's `_reconstruct_text`
 * exactly (see that file — ground truth) so a valid result here is always
 * accepted by the backend's validate_passage.
 *
 * Deviation note: rather than reading Selection.anchorNode/focusNode (which
 * preserve user drag direction) and manually swapping them, this reads the
 * Selection's Range (`getRangeAt(0)`), whose start/end are already
 * normalized to document order by the DOM Range API regardless of drag
 * direction — so no separate "backward selection" branch is needed; the
 * normalization is inherent in using Range instead of anchor/focus. */
export function passageFromSelection(
  selection: Selection | null,
  blocks: SelectionBlock[],
): Passage | undefined {
  if (!selection || selection.isCollapsed || selection.rangeCount === 0) return undefined;

  const range = selection.getRangeAt(0);
  const startEl = findBlockElement(range.startContainer);
  const endEl = findBlockElement(range.endContainer);
  if (!startEl || !endEl) return undefined;

  if (countTextNodes(startEl) !== 1) return undefined;
  if (endEl !== startEl && countTextNodes(endEl) !== 1) return undefined;

  const startBlockId = startEl.dataset.blockId;
  const endBlockId = endEl.dataset.blockId;
  if (!startBlockId || !endBlockId) return undefined;

  const blocksById = new Map(blocks.map((b) => [b.block_id, b]));
  const startBlock = blocksById.get(startBlockId);
  const endBlock = blocksById.get(endBlockId);
  if (!startBlock || !endBlock) return undefined;

  const startOffset = codePointIndex(startBlock.text, range.startOffset);
  const endOffset = codePointIndex(endBlock.text, range.endOffset);

  if (startBlockId === endBlockId) {
    if (startOffset >= endOffset) return undefined;
    return {
      first_block_id: startBlockId,
      first_block_offset: startOffset,
      last_block_id: endBlockId,
      last_block_offset: endOffset,
      text: codePointSlice(startBlock.text, startOffset, endOffset),
    };
  }

  if (startBlockId > endBlockId) return undefined;

  const orderedIds = blocks.map((b) => b.block_id);
  const startIndex = orderedIds.indexOf(startBlockId);
  const endIndex = orderedIds.indexOf(endBlockId);
  const intervening = blocks.slice(startIndex + 1, endIndex);

  const pieces = [
    codePointSlice(startBlock.text, startOffset),
    ...intervening.map((b) => b.text),
    codePointSlice(endBlock.text, 0, endOffset),
  ];

  return {
    first_block_id: startBlockId,
    first_block_offset: startOffset,
    last_block_id: endBlockId,
    last_block_offset: endOffset,
    text: pieces.join(JOIN),
  };
}

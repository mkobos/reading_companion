import type { components } from "../api/types";
import { codePointIndex, codePointSlice } from "./textOffsets";

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

/** Maps a DOM Range endpoint (a text node + a local UTF-16 offset within
 * it) to its absolute UTF-16 offset within `el`'s full text content. A
 * block normally renders as a single text node, but Block.tsx's
 * `highlight` prop splits it into up to three sibling text nodes
 * (pre/mark-child/post) — walking all of `el`'s text nodes in DOM order
 * and summing the lengths of those before `textNode` keeps offsets
 * correct regardless of how many text nodes the block currently has. */
function absoluteOffsetInBlock(el: Element, textNode: Node, localOffset: number): number {
  let total = 0;
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let node: Node | null;
  while ((node = walker.nextNode())) {
    if (node === textNode) return total + localOffset;
    total += (node.textContent ?? "").length;
  }
  return total + localOffset;
}

/** Derives a Passage from the current window Selection, or undefined if the
 * selection is empty/collapsed/outside any block. Mirrors
 * backend/app/passages.py's `_reconstruct_text` exactly (see that file —
 * ground truth) so a valid result here is always accepted by the backend's
 * validate_passage.
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

  const startBlockId = startEl.dataset.blockId;
  const endBlockId = endEl.dataset.blockId;
  if (!startBlockId || !endBlockId) return undefined;

  const blocksById = new Map(blocks.map((b) => [b.block_id, b]));
  const startBlock = blocksById.get(startBlockId);
  const endBlock = blocksById.get(endBlockId);
  if (!startBlock || !endBlock) return undefined;

  const startUtf16Offset = absoluteOffsetInBlock(startEl, range.startContainer, range.startOffset);
  const endUtf16Offset = absoluteOffsetInBlock(endEl, range.endContainer, range.endOffset);
  const startOffset = codePointIndex(startBlock.text, startUtf16Offset);
  const endOffset = codePointIndex(endBlock.text, endUtf16Offset);

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

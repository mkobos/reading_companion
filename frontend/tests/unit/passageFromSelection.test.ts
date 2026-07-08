import { afterEach, describe, expect, it } from "vitest";
import { passageFromSelection } from "../../src/document/passageFromSelection";

const BLOCKS = [
  { block_id: "000000", text: "Hello world" },
  { block_id: "000001", text: "Second paragraph here." },
  { block_id: "000002", text: "Third one." },
];

function renderBlocks(blocks: { block_id: string; text: string }[]) {
  const container = document.createElement("div");
  for (const block of blocks) {
    const el = document.createElement("p");
    el.setAttribute("data-block-id", block.block_id);
    el.appendChild(document.createTextNode(block.text));
    container.appendChild(el);
  }
  document.body.appendChild(container);
  return container;
}

function selectRange(
  container: HTMLElement,
  startBlockId: string,
  startOffset: number,
  endBlockId: string,
  endOffset: number,
  backward = false,
) {
  const startEl = container.querySelector(`[data-block-id="${startBlockId}"]`)!;
  const endEl = container.querySelector(`[data-block-id="${endBlockId}"]`)!;
  const startNode = startEl.firstChild!;
  const endNode = endEl.firstChild!;

  const selection = window.getSelection()!;
  selection.removeAllRanges();
  if (backward) {
    selection.setBaseAndExtent(endNode, endOffset, startNode, startOffset);
  } else {
    selection.setBaseAndExtent(startNode, startOffset, endNode, endOffset);
  }
  return selection;
}

afterEach(() => {
  document.body.innerHTML = "";
  window.getSelection()?.removeAllRanges();
});

describe("passageFromSelection", () => {
  it("returns undefined for a null selection", () => {
    expect(passageFromSelection(null, BLOCKS)).toBeUndefined();
  });

  it("returns undefined for a collapsed selection", () => {
    const container = renderBlocks(BLOCKS);
    const selection = selectRange(container, "000000", 2, "000000", 2);
    expect(passageFromSelection(selection, BLOCKS)).toBeUndefined();
  });

  it("builds a single-block ASCII passage", () => {
    const container = renderBlocks(BLOCKS);
    const selection = selectRange(container, "000000", 0, "000000", 5);
    const passage = passageFromSelection(selection, BLOCKS);
    expect(passage).toEqual({
      first_block_id: "000000",
      first_block_offset: 0,
      last_block_id: "000000",
      last_block_offset: 5,
      text: "Hello",
    });
  });

  it("produces the same passage regardless of drag direction (backward selection normalization)", () => {
    const container = renderBlocks(BLOCKS);
    const forward = passageFromSelection(selectRange(container, "000000", 0, "000000", 5), BLOCKS);
    document.body.innerHTML = "";
    const container2 = renderBlocks(BLOCKS);
    const backward = passageFromSelection(
      selectRange(container2, "000000", 0, "000000", 5, true),
      BLOCKS,
    );
    expect(backward).toEqual(forward);
  });

  it("computes code-point offsets correctly across a surrogate-pair emoji", () => {
    const blocks = [{ block_id: "000000", text: "a😀b" }];
    const container = renderBlocks(blocks);
    // UTF-16 offsets: 'a'=0, emoji=1..2 (surrogate pair), 'b'=3. Select from
    // just after 'a' (utf16 offset 1) to just after 'b' (utf16 offset 4).
    const selection = selectRange(container, "000000", 1, "000000", 4);
    const passage = passageFromSelection(selection, blocks);
    expect(passage).toEqual({
      first_block_id: "000000",
      first_block_offset: 1,
      last_block_id: "000000",
      last_block_offset: 3,
      text: "😀b",
    });
  });

  it("joins multi-block selections with \\n, matching the backend's reconstruction algorithm", () => {
    const container = renderBlocks(BLOCKS);
    const selection = selectRange(container, "000000", 6, "000002", 5);
    const passage = passageFromSelection(selection, BLOCKS);
    expect(passage).toEqual({
      first_block_id: "000000",
      first_block_offset: 6,
      last_block_id: "000002",
      last_block_offset: 5,
      text: "world\nSecond paragraph here.\nThird",
    });
  });

  it("returns undefined when an endpoint has no block ancestor", () => {
    const container = renderBlocks(BLOCKS);
    const outside = document.createElement("span");
    outside.textContent = "outside text";
    document.body.appendChild(outside);

    const startEl = container.querySelector('[data-block-id="000000"]')!;
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.setBaseAndExtent(startEl.firstChild!, 0, outside.firstChild!, 3);

    expect(passageFromSelection(selection, BLOCKS)).toBeUndefined();
  });

  it("returns undefined when a block's DOM node has more than one text node", () => {
    const container = document.createElement("div");
    const el = document.createElement("p");
    el.setAttribute("data-block-id", "000000");
    el.appendChild(document.createTextNode("Hello "));
    el.appendChild(document.createTextNode("world"));
    container.appendChild(el);
    document.body.appendChild(container);

    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.setBaseAndExtent(el.childNodes[0]!, 0, el.childNodes[1]!, 3);

    expect(passageFromSelection(selection, [{ block_id: "000000", text: "Hello world" }])).toBeUndefined();
  });
});

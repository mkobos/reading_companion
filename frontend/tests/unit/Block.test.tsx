import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Block } from "../../src/document/Block";
import type { components } from "../../src/api/types";

type BlockData = components["schemas"]["Block"];

describe("Block", () => {
  it("renders a paragraph as a <p> with data-block-id", () => {
    const block: BlockData = { block_id: "000000", type: "paragraph", text: "Hello world" };
    render(<Block block={block} />);
    const el = screen.getByText("Hello world");
    expect(el.tagName).toBe("P");
    expect(el).toHaveAttribute("data-block-id", "000000");
  });

  // passageFromSelection.ts assumes exactly one text node per block (React
  // renders `{block.text}` as a single child) — verify that invariant holds
  // for a representative block type, since selection-to-Passage conversion
  // silently aborts (returns undefined) otherwise.
  it("renders exactly one text-node child for a paragraph block", () => {
    const block: BlockData = { block_id: "000000", type: "paragraph", text: "Hello world" };
    render(<Block block={block} />);
    const el = screen.getByText("Hello world");
    expect(el.childNodes.length).toBe(1);
    expect(el.childNodes[0]?.nodeType).toBe(Node.TEXT_NODE);
  });

  it("renders a heading with the given level as h1..h6", () => {
    const block: BlockData = { block_id: "000001", type: "heading", text: "Title", level: 2 };
    render(<Block block={block} />);
    const el = screen.getByText("Title");
    expect(el.tagName).toBe("H2");
  });

  it("renders a list_item as <li>", () => {
    const block: BlockData = { block_id: "000002", type: "list_item", text: "item one" };
    render(<Block block={block} />);
    expect(screen.getByText("item one").tagName).toBe("LI");
  });

  it("renders a code_block as <pre><code>", () => {
    const block: BlockData = { block_id: "000003", type: "code_block", text: "const x = 1;" };
    render(<Block block={block} />);
    const el = screen.getByText("const x = 1;");
    expect(el.tagName).toBe("CODE");
    expect(el.closest("pre")).not.toBeNull();
  });

  it("renders a blockquote as <blockquote>", () => {
    const block: BlockData = { block_id: "000004", type: "blockquote", text: "quoted" };
    render(<Block block={block} />);
    expect(screen.getByText("quoted").tagName).toBe("BLOCKQUOTE");
  });
});

describe("Block XSS safety", () => {
  it("renders script-tag-like text as inert visible text, never as executed HTML", () => {
    const malicious = "<script>window.__xss = true;</script>";
    const block: BlockData = { block_id: "000005", type: "paragraph", text: malicious };
    const { container } = render(<Block block={block} />);

    // The literal text must be visible...
    expect(screen.getByText(malicious)).toBeInTheDocument();
    // ...and must never have been parsed into a real <script> element.
    expect(container.querySelector("script")).toBeNull();
    expect((window as unknown as { __xss?: boolean }).__xss).toBeUndefined();
  });
});

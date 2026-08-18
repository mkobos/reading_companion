import type { JSX, ReactNode } from "react";
import type { components } from "../api/types";
import { codePointSlice } from "./textOffsets";

type BlockData = components["schemas"]["Block"];

const HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"] as const;

/** Code-point offset range (local to this block's `text`) to render wrapped
 * in a <mark>, e.g. when the user clicks a discussion box anchored to this
 * passage. */
export interface BlockHighlight {
  start: number;
  end: number;
}

/** Renders `text` as-is when no highlight is given (a single React text
 * child, as passageFromSelection.ts's DOM-offset math expects for the
 * common case), or split into pre/<mark>/post text when a highlight range
 * is given. */
function renderText(text: string, highlight?: BlockHighlight): ReactNode {
  if (!highlight) return text;
  return (
    <>
      {codePointSlice(text, 0, highlight.start)}
      <mark className="rounded-sm bg-amber-200/70 px-0.5">
        {codePointSlice(text, highlight.start, highlight.end)}
      </mark>
      {codePointSlice(text, highlight.end)}
    </>
  );
}

/** Renders one Block by type→semantic element. `block.text` is untrusted
 * plain text (already flattened/sanitized server-side) and is placed as a
 * React text child only — never injected as raw HTML, never re-parsed
 * as Markdown/HTML. See Phase 1 plan §6.1. */
export function Block({ block, highlight }: { block: BlockData; highlight?: BlockHighlight }) {
  const props = { "data-block-id": block.block_id };
  const content = renderText(block.text, highlight);

  switch (block.type) {
    case "heading": {
      const level = block.level && block.level >= 1 && block.level <= 6 ? block.level : 1;
      const Tag = HEADING_TAGS[level - 1] as keyof JSX.IntrinsicElements;
      return <Tag {...props}>{content}</Tag>;
    }
    case "list_item":
      return <li {...props}>{content}</li>;
    case "code_block":
      return (
        <pre {...props}>
          <code>{content}</code>
        </pre>
      );
    case "blockquote":
      return <blockquote {...props}>{content}</blockquote>;
    case "paragraph":
    default:
      return <p {...props}>{content}</p>;
  }
}

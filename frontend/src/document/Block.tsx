import type { JSX } from "react";
import type { components } from "../api/types";

type BlockData = components["schemas"]["Block"];

const HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"] as const;

/** Renders one Block by type→semantic element. `block.text` is untrusted
 * plain text (already flattened/sanitized server-side) and is placed as a
 * React text child only — never injected as raw HTML, never re-parsed
 * as Markdown/HTML. See Phase 1 plan §6.1. */
export function Block({ block }: { block: BlockData }) {
  const props = { "data-block-id": block.block_id };

  switch (block.type) {
    case "heading": {
      const level = block.level && block.level >= 1 && block.level <= 6 ? block.level : 1;
      const Tag = HEADING_TAGS[level - 1] as keyof JSX.IntrinsicElements;
      return <Tag {...props}>{block.text}</Tag>;
    }
    case "list_item":
      return <li {...props}>{block.text}</li>;
    case "code_block":
      return (
        <pre {...props}>
          <code>{block.text}</code>
        </pre>
      );
    case "blockquote":
      return <blockquote {...props}>{block.text}</blockquote>;
    case "paragraph":
    default:
      return <p {...props}>{block.text}</p>;
  }
}

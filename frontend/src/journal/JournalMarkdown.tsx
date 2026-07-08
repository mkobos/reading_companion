import ReactMarkdown, { type Components } from "react-markdown";

// Links render as inert plain text (product decision, no clickable links —
// journal Markdown is untrusted LLM output and this is the app's first
// Markdown-rendering surface). No rehype-raw / allowDangerousHtml anywhere,
// so raw HTML in the source is never rendered as live DOM either.
const components: Components = {
  a: ({ children }) => <>{children}</>,
};

/** Renders the reading journal's Markdown text safely: default remark/
 * rehype plugins only, no raw-HTML injection anywhere. */
export function JournalMarkdown({ text }: { text: string }) {
  return (
    <div className="space-y-2">
      <ReactMarkdown components={components}>{text}</ReactMarkdown>
    </div>
  );
}

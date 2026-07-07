"""Document -> Block parsing.

Rules and the exact block-construct mapping are specified in
spec/features/document-upload.feature and
spec/technical_specification.md §5 ("Upload safety").
"""

from dataclasses import dataclass

from markdown_it import MarkdownIt
from markdown_it.token import Token

BlockType = str  # one of: heading, paragraph, list_item, code_block, blockquote


@dataclass(frozen=True)
class Block:
    block_id: str
    type: BlockType
    text: str
    level: int | None = None


def _next_id(index: int) -> str:
    return f"{index:06d}"


def _flatten_inline(children: list[Token] | None) -> str:
    """Render inline tokens to plain text.

    Raw HTML is dropped; links/emphasis/code spans flatten to their inner
    text (open/close marker tokens carry no text of their own); images
    contribute their alt text.
    """
    if not children:
        return ""

    parts: list[str] = []
    for child in children:
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type == "image":
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
        # html_inline, link_open/close, strong_open/close, em_open/close,
        # etc. contribute nothing themselves.
    return "".join(parts).strip()


def _md() -> MarkdownIt:
    # "table" is a GFM extension, disabled by the strict commonmark preset.
    md = MarkdownIt("commonmark").enable("table")
    # markdown-it-py's default link-URL validator rejects unsafe schemes
    # (e.g. javascript:) by leaving the markup unparsed as literal text.
    # We want the opposite: parse it as a link so _flatten_inline can
    # flatten it to plain text and discard the href entirely — safe because
    # no code path here ever reads or emits a link's URL.
    md.validateLink = lambda url: True
    return md


def parse_markdown(content: str) -> list[Block]:
    tokens = _md().parse(content)
    blocks: list[Block] = []
    next_index = 0

    def add(type_: BlockType, text: str, level: int | None = None) -> None:
        nonlocal next_index
        if not text:
            return
        blocks.append(Block(_next_id(next_index), type_, text, level))
        next_index += 1

    list_item_paragraph_counts: list[int] = []
    blockquote_depth = 0
    table_row_cells: list[str] | None = None

    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]
        ty = token.type

        if ty == "heading_open":
            level = int(token.tag[1:])
            add("heading", _flatten_inline(tokens[i + 1].children), level)
            i += 3  # heading_open, inline, heading_close
            continue

        if ty == "blockquote_open":
            blockquote_depth += 1
            i += 1
            continue
        if ty == "blockquote_close":
            blockquote_depth -= 1
            i += 1
            continue

        if ty == "list_item_open":
            list_item_paragraph_counts.append(0)
            i += 1
            continue
        if ty == "list_item_close":
            list_item_paragraph_counts.pop()
            i += 1
            continue

        if ty == "paragraph_open":
            text = _flatten_inline(tokens[i + 1].children)
            if list_item_paragraph_counts:
                # First paragraph in a list item is the list_item block;
                # any further paragraphs in the same item are plain
                # paragraphs that follow it.
                is_first_in_item = list_item_paragraph_counts[-1] == 0
                list_item_paragraph_counts[-1] += 1
                add("list_item" if is_first_in_item else "paragraph", text)
            elif blockquote_depth:
                add("blockquote", text)
            else:
                add("paragraph", text)
            i += 3  # paragraph_open, inline, paragraph_close
            continue

        if ty in ("fence", "code_block"):
            add("code_block", token.content.rstrip("\n"))
            i += 1
            continue

        if ty == "tr_open":
            table_row_cells = []
            i += 1
            continue
        if ty == "tr_close":
            add("paragraph", " | ".join(table_row_cells or []))
            table_row_cells = None
            i += 1
            continue
        if ty in ("th_open", "td_open"):
            assert table_row_cells is not None
            table_row_cells.append(_flatten_inline(tokens[i + 1].children))
            i += 3  # th_open/td_open, inline, th_close/td_close
            continue

        # Dropped entirely, no block emitted: hr (thematic break), raw HTML
        # blocks, and pure structural tokens (list/table container
        # open/close, table head/body sections) that carry no text.
        i += 1

    return blocks


def parse_plain_text(content: str) -> list[Block]:
    """Plain-text files bypass the Markdown parser: split into paragraphs on
    blank lines; single newlines within a paragraph join with a space."""
    paragraphs = content.strip().split("\n\n")
    blocks: list[Block] = []
    index = 0
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        text = " ".join(line.strip() for line in paragraph.splitlines())
        blocks.append(Block(_next_id(index), "paragraph", text))
        index += 1
    return blocks

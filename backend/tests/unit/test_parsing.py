from app.parsing import Block, parse_markdown, parse_plain_text


def _as_tuples(blocks: list[Block]) -> list[tuple]:
    return [(b.block_id, b.type, b.text, b.level) for b in blocks]


def test_markdown_structure_maps_to_typed_blocks():
    markdown = (
        "# Intro to BDD\n"
        "BDD is collaboration-first.\n"
        "* List item 1\n"
        "\n"
        "```python\n"
        'print("code")\n'
        "```\n"
        "> A blockquote.\n"
    )

    blocks = parse_markdown(markdown)

    assert _as_tuples(blocks) == [
        ("000000", "heading", "Intro to BDD", 1),
        ("000001", "paragraph", "BDD is collaboration-first.", None),
        ("000002", "list_item", "List item 1", None),
        ("000003", "code_block", 'print("code")', None),
        ("000004", "blockquote", "A blockquote.", None),
    ]


def test_markdown_constructs_without_own_block_type_are_flattened():
    markdown = (
        "| Name | Role     |\n"
        "| ---- | -------- |\n"
        "| Ada  | Engineer |\n"
        "\n"
        "---\n"
        "\n"
        "![A portrait of Ada](ada.png)\n"
        "\n"
        "* Outer item\n"
        "  * Nested **bold** item\n"
    )

    blocks = parse_markdown(markdown)

    assert _as_tuples(blocks) == [
        ("000000", "paragraph", "Name | Role", None),
        ("000001", "paragraph", "Ada | Engineer", None),
        ("000002", "paragraph", "A portrait of Ada", None),
        ("000003", "list_item", "Outer item", None),
        ("000004", "list_item", "Nested bold item", None),
    ]


def test_plain_text_is_split_into_paragraph_blocks():
    text = (
        "First paragraph line one.\n"
        "Continues on line two.\n"
        "\n"
        "Second paragraph text.\n"
    )

    blocks = parse_plain_text(text)

    assert _as_tuples(blocks) == [
        (
            "000000",
            "paragraph",
            "First paragraph line one. Continues on line two.",
            None,
        ),
        ("000001", "paragraph", "Second paragraph text.", None),
    ]


def test_markdown_syntax_in_plain_text_stays_literal():
    text = "# Not a heading\n"

    blocks = parse_plain_text(text)

    assert _as_tuples(blocks) == [
        ("000000", "paragraph", "# Not a heading", None),
    ]


def test_malicious_markdown_content_is_neutralized():
    markdown = (
        "<script>alert('inject')</script>\n"
        "\n"
        "[Click me](javascript:alert(1))\n"
        "\n"
        "Plain text.\n"
    )

    blocks = parse_markdown(markdown)

    assert _as_tuples(blocks) == [
        ("000000", "paragraph", "Click me", None),
        ("000001", "paragraph", "Plain text.", None),
    ]

    for block in blocks:
        assert "javascript:" not in block.text
        assert "<script>" not in block.text

Feature: Document upload and parsing
  A workspace holds exactly one immutable document.
  Only plain text and Markdown are accepted.
  Validation and parsing happen server-side before anything is stored
  (user-spec §5, upload safety).

  Background:
    Given an empty workspace "W" with no document

  Scenario Outline: Accepted formats
    When the user uploads a valid <format> file within the size limit
    Then the raw file is stored in blob storage under workspace "W"
    And the file is parsed into an ordered list of typed blocks
    And the parsed blocks are persisted with stable sequential block IDs
    And the reading view opens showing the document from the beginning

    Examples:
      | format     |
      | plain text |
      | Markdown   |

  Scenario: Markdown structure maps to typed blocks
    When the user uploads a Markdown file with content:
      """markdown
      # Intro to BDD
      BDD is collaboration-first.
      * List item 1
      
      ```python
      print("code")
      ```
      > A blockquote.
      """
    Then the document is parsed into the following ordered blocks:
      | block_id | type       | text                        | level |
      | 000000   | heading    | Intro to BDD                | 1     |
      | 000001   | paragraph  | BDD is collaboration-first. |       |
      | 000002   | list_item  | List item 1                 |       |
      | 000003   | code_block | print("code")               |       |
      | 000004   | blockquote | A blockquote.               |       |
    And no raw HTML is preserved in the blocks

  Scenario: Markdown constructs without a block type of their own are flattened
    Block-construct mapping: a table becomes one paragraph block per row
    (cell texts joined with " | "); thematic breaks and link reference
    definitions are dropped; an image becomes a paragraph holding its alt
    text (dropped when the alt text is empty); nested lists are flattened
    into a linear sequence of list_item blocks in document order; extra
    paragraphs inside a list item become separate paragraph blocks after it.
    Inline formatting (emphasis, links, code spans) flattens to plain text.

    When the user uploads a Markdown file with content:
      """markdown
      | Name | Role     |
      | ---- | -------- |
      | Ada  | Engineer |

      ---

      ![A portrait of Ada](ada.png)

      * Outer item
        * Nested **bold** item
      """
    Then the document is parsed into the following ordered blocks:
      | block_id | type      | text                |
      | 000000   | paragraph | Name \| Role        |
      | 000001   | paragraph | Ada \| Engineer     |
      | 000002   | paragraph | A portrait of Ada   |
      | 000003   | list_item | Outer item          |
      | 000004   | list_item | Nested bold item    |

  Scenario: Plain text is split into paragraph blocks
    Plain text files do not go through the Markdown parser. They are split
    into paragraphs on blank lines; single newlines within a paragraph are
    joined with a space.

    When the user uploads a plain text file with content:
      """
      First paragraph line one.
      Continues on line two.

      Second paragraph text.
      """
    Then the document is parsed into the following ordered blocks:
      | block_id | type      | text                                          |
      | 000000   | paragraph | First paragraph line one. Continues on line two. |
      | 000001   | paragraph | Second paragraph text.                        |

  Scenario: Markdown syntax in a plain text file stays literal
    When the user uploads a plain text file with content:
      """
      # Not a heading
      """
    Then the document is parsed into the following ordered blocks:
      | block_id | type      | text            |
      | 000000   | paragraph | # Not a heading |

  Scenario: Rejecting an unsupported file type
    When the user uploads a file with a disallowed extension or content type
    Then the upload is rejected with a message naming the supported formats
    And nothing is stored in the blob store or document store

  Scenario: Rejecting an oversized file
    When the user uploads a file exceeding the configured size limit
    Then the upload is rejected before the body is fully processed
    And the message states the size limit

  Scenario: Rejecting invalid text encoding
    When the user uploads a file that is not valid UTF-8 text
    Then the upload is rejected with an encoding error message
    And nothing is stored

  Scenario: Malicious Markdown content is neutralized
    Sanitization rule: raw HTML (blocks and inlines) is dropped entirely;
    links and other inline formatting flatten to their plain text, so any
    URL (including javascript: URLs) is discarded.

    When the user uploads a Markdown file with content:
      """markdown
      <script>alert('inject')</script>

      [Click me](javascript:alert(1))

      Plain text.
      """
    Then parsing succeeds with raw HTML dropped and links flattened to their text:
      | block_id | type      | text        |
      | 000000   | paragraph | Click me    |
      | 000001   | paragraph | Plain text. |
    And the rendered reading view does not execute any script or active link

  Scenario: Document is immutable once uploaded
    Given workspace "W" already has a document
    When the user attempts to upload another document to workspace "W"
    Then the upload is rejected
    And the user is directed to create a new workspace for a new document

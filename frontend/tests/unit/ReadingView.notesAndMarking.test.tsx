import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { ReadingView } from "../../src/document/ReadingView";
import { server } from "../msw/server";

const ANCHOR = {
  first_block_id: "000000",
  first_block_offset: 0,
  last_block_id: "000000",
  last_block_offset: 5,
  text: "First",
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

function mockDocument() {
  server.use(
    http.get("/api/workspaces/ws1/document", () =>
      HttpResponse.json({
        filename: "doc.md",
        format: "markdown",
        size_bytes: 42,
        uploaded_at: "2026-01-01T00:00:00Z",
        blocks: [
          { block_id: "000000", type: "paragraph", text: "First paragraph." },
          { block_id: "000001", type: "paragraph", text: "Second paragraph." },
        ],
      }),
    ),
  );
}

describe("ReadingView note indicators", () => {
  it("renders a NoteIndicator for a note anchored to a visible block, and calls onSelectNote when clicked", async () => {
    mockDocument();
    const user = userEvent.setup();
    const onSelectNote = vi.fn();
    const note = {
      note_id: "n1",
      anchor: ANCHOR,
      text: "my note",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };

    renderWithClient(<ReadingView workspaceId="ws1" notes={[note]} onSelectNote={onSelectNote} />);

    await screen.findByText("First paragraph.");
    const indicator = screen.getByTestId("note-indicator-n1");
    await user.click(indicator);
    expect(onSelectNote).toHaveBeenCalledWith("n1");
  });
});

describe("ReadingView passage marking", () => {
  it("calls onPassageMarked with a Passage when text is selected and mouseup fires", async () => {
    mockDocument();
    const onPassageMarked = vi.fn();

    renderWithClient(<ReadingView workspaceId="ws1" onPassageMarked={onPassageMarked} />);

    const firstParagraph = await screen.findByText("First paragraph.");
    const textNode = firstParagraph.firstChild!;

    const range = document.createRange();
    range.setStart(textNode, 0);
    range.setEnd(textNode, 5);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    firstParagraph.closest("[data-testid='reading-view']")!.dispatchEvent(
      new MouseEvent("mouseup", { bubbles: true }),
    );

    expect(onPassageMarked).toHaveBeenCalledWith({
      first_block_id: "000000",
      first_block_offset: 0,
      last_block_id: "000000",
      last_block_offset: 5,
      text: "First",
    });
  });

  it("renders a SuggestionsPopover when markedPassage is provided", async () => {
    mockDocument();
    server.use(
      http.post("/api/workspaces/ws1/suggestions", () =>
        HttpResponse.json({ suggestions: ["Q1?", "Q2?", "Q3?", "Q4?"] }),
      ),
    );

    renderWithClient(<ReadingView workspaceId="ws1" markedPassage={ANCHOR} onPassageMarked={() => {}} />);

    await screen.findByText("First paragraph.");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { ReadingView } from "../../src/document/ReadingView";
import { server } from "../msw/server";

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ReadingView", () => {
  it("renders blocks in array order with stable block ids", async () => {
    server.use(
      http.get("/api/workspaces/ws1/document", () =>
        HttpResponse.json({
          filename: "doc.md",
          format: "markdown",
          size_bytes: 42,
          uploaded_at: "2026-01-01T00:00:00Z",
          blocks: [
            { block_id: "000000", type: "heading", text: "Title", level: 1 },
            { block_id: "000001", type: "paragraph", text: "First paragraph." },
            { block_id: "000002", type: "paragraph", text: "Second paragraph." },
          ],
        }),
      ),
    );

    renderWithClient(<ReadingView workspaceId="ws1" />);

    const title = await screen.findByText("Title");
    const first = screen.getByText("First paragraph.");
    const second = screen.getByText("Second paragraph.");

    // DOM order matches array order.
    expect(
      title.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    expect(title).toHaveAttribute("data-block-id", "000000");
    expect(first).toHaveAttribute("data-block-id", "000001");
    expect(second).toHaveAttribute("data-block-id", "000002");
  });
});

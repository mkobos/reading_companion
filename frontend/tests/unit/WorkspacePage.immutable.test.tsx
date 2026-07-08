import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { WorkspacePage } from "../../src/workspace/WorkspacePage";
import { server } from "../msw/server";

function renderPage(workspaceId: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/w/${workspaceId}`]}>
        <Routes>
          <Route path="/w/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkspacePage immutability", () => {
  it("does not render the upload UI once has_document is true", async () => {
    server.use(
      http.get("/api/workspaces/ws1", () =>
        HttpResponse.json({
          workspace_id: "ws1",
          created_at: "2026-01-01T00:00:00Z",
          has_document: true,
          note_count: 0,
          discussion_count: 0,
          has_journal: false,
        }),
      ),
      http.get("/api/workspaces/ws1/document", () =>
        HttpResponse.json({
          filename: "doc.md",
          format: "markdown",
          size_bytes: 10,
          uploaded_at: "2026-01-01T00:00:00Z",
          blocks: [{ block_id: "000000", type: "paragraph", text: "content" }],
        }),
      ),
    );

    renderPage("ws1");

    expect(await screen.findByText("content")).toBeInTheDocument();
    expect(screen.queryByLabelText(/upload/i)).toBeNull();
  });

  it("renders the upload UI when has_document is false", async () => {
    server.use(
      http.get("/api/workspaces/ws2", () =>
        HttpResponse.json({
          workspace_id: "ws2",
          created_at: "2026-01-01T00:00:00Z",
          has_document: false,
          note_count: 0,
          discussion_count: 0,
          has_journal: false,
        }),
      ),
    );

    renderPage("ws2");

    expect(await screen.findByLabelText(/upload/i)).toBeInTheDocument();
  });
});

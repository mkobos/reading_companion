import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { NotesTab } from "../../src/note/NotesTab";
import { server } from "../msw/server";

const ANCHOR = {
  first_block_id: "000000",
  first_block_offset: 0,
  last_block_id: "000000",
  last_block_offset: 5,
  text: "hello",
};

function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("NotesTab", () => {
  it("shows a hint instead of a composer when no passage is marked", async () => {
    server.use(http.get("/api/workspaces/ws1/notes", () => HttpResponse.json([])));
    renderWithClient(<NotesTab workspaceId="ws1" />);
    expect(await screen.findByText(/select text/i)).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("shows a composer anchored to the marked passage and creates a note", async () => {
    server.use(
      http.get("/api/workspaces/ws1/notes", () => HttpResponse.json([])),
      http.post("/api/workspaces/ws1/notes", () =>
        HttpResponse.json(
          {
            note_id: "n1",
            anchor: ANCHOR,
            text: "hi",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
          { status: 201 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onMarkHandled = vi.fn();
    renderWithClient(<NotesTab workspaceId="ws1" markedPassage={ANCHOR} onMarkHandled={onMarkHandled} />);

    await user.type(screen.getByRole("textbox"), "hi");
    await user.click(screen.getByRole("button", { name: /add note/i }));

    await waitFor(() => expect(onMarkHandled).toHaveBeenCalled());
  });

  it("renders existing notes and deletes one via the confirm dialog", async () => {
    server.use(
      http.get("/api/workspaces/ws1/notes", () =>
        HttpResponse.json([
          {
            note_id: "n1",
            anchor: ANCHOR,
            text: "hi",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
      ),
      http.delete("/api/workspaces/ws1/notes/n1", () => new HttpResponse(null, { status: 204 })),
    );
    const user = userEvent.setup();
    renderWithClient(<NotesTab workspaceId="ws1" />);

    await screen.findByText("hi");
    await user.click(screen.getByRole("button", { name: /delete/i }));
    const dialog = screen.getByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /delete/i }));

    await waitFor(() => expect(screen.queryByText("hi")).toBeNull());
  });
});

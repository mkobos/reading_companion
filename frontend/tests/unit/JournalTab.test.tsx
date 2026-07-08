import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { JournalTab } from "../../src/journal/JournalTab";
import { server } from "../msw/server";

function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("JournalTab", () => {
  it("shows a CTA when there is no journal yet (404)", async () => {
    server.use(http.get("/api/workspaces/ws1/journal", () => new HttpResponse(null, { status: 404 })));
    renderWithClient(<JournalTab workspaceId="ws1" />);
    expect(await screen.findByRole("button", { name: /generate a reading journal/i })).toBeInTheDocument();
  });

  it("generates and renders the journal via markdown", async () => {
    server.use(
      http.get("/api/workspaces/ws1/journal", () => new HttpResponse(null, { status: 404 })),
      http.post("/api/workspaces/ws1/journal", () =>
        HttpResponse.json({ text: "## Reading Journal\n\nSome content.", generated_at: "2026-01-01T00:00:00Z" }),
      ),
    );
    const user = userEvent.setup();
    renderWithClient(<JournalTab workspaceId="ws1" />);

    await user.click(await screen.findByRole("button", { name: /generate a reading journal/i }));

    expect(await screen.findByRole("heading", { name: "Reading Journal" })).toBeInTheDocument();
    expect(screen.getByText("Some content.")).toBeInTheDocument();
  });

  it("shows a specific message on a 409 (nothing to synthesize)", async () => {
    server.use(
      http.get("/api/workspaces/ws1/journal", () => new HttpResponse(null, { status: 404 })),
      http.post("/api/workspaces/ws1/journal", () => new HttpResponse(null, { status: 409 })),
    );
    const user = userEvent.setup();
    renderWithClient(<JournalTab workspaceId="ws1" />);

    await user.click(await screen.findByRole("button", { name: /generate a reading journal/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/nothing to reflect/i);
  });

  it("on a 503 during regeneration, keeps the previous journal visible and shows an error", async () => {
    let calls = 0;
    server.use(
      http.get("/api/workspaces/ws1/journal", () =>
        HttpResponse.json({ text: "Old journal text.", generated_at: "2026-01-01T00:00:00Z" }),
      ),
      http.post("/api/workspaces/ws1/journal", () => {
        calls += 1;
        return new HttpResponse(null, { status: 503 });
      }),
    );
    const user = userEvent.setup();
    renderWithClient(<JournalTab workspaceId="ws1" />);

    await screen.findByText("Old journal text.");
    await user.click(screen.getByRole("button", { name: /regenerate journal/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Old journal text.")).toBeInTheDocument();
    expect(calls).toBe(1);
  });
});

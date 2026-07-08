import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { SuggestionsPopover } from "../../src/document/SuggestionsPopover";
import { server } from "../msw/server";

const PASSAGE = {
  first_block_id: "000000",
  first_block_offset: 0,
  last_block_id: "000000",
  last_block_offset: 5,
  text: "hello",
};
const VIEWPORT = { first_block_id: "000000", last_block_id: "000001" };

function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("SuggestionsPopover", () => {
  it("renders 4 suggestions from a successful call", async () => {
    server.use(
      http.post("/api/workspaces/ws1/suggestions", () =>
        HttpResponse.json({ suggestions: ["Q1?", "Q2?", "Q3?", "Q4?"] }),
      ),
    );

    renderWithClient(
      <SuggestionsPopover workspaceId="ws1" passage={PASSAGE} viewport={VIEWPORT} onDismiss={() => {}} />,
    );

    await waitFor(() => expect(screen.getByText("Q1?")).toBeInTheDocument());
    expect(screen.getByText("Q2?")).toBeInTheDocument();
    expect(screen.getByText("Q3?")).toBeInTheDocument();
    expect(screen.getByText("Q4?")).toBeInTheDocument();
  });

  it("shows a free-form fallback input on a 503", async () => {
    server.use(http.post("/api/workspaces/ws1/suggestions", () => new HttpResponse(null, { status: 503 })));

    renderWithClient(
      <SuggestionsPopover workspaceId="ws1" passage={PASSAGE} viewport={VIEWPORT} onDismiss={() => {}} />,
    );

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("shows the retry-after wait time on a 429", async () => {
    server.use(
      http.post("/api/workspaces/ws1/suggestions", () =>
        HttpResponse.json({ message: "rate limited" }, { status: 429, headers: { "Retry-After": "9" } }),
      ),
    );

    renderWithClient(
      <SuggestionsPopover workspaceId="ws1" passage={PASSAGE} viewport={VIEWPORT} onDismiss={() => {}} />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(/9s/);
  });

  it("calls onDismiss without any residual API calls when dismissed", async () => {
    let callCount = 0;
    server.use(
      http.post("/api/workspaces/ws1/suggestions", () => {
        callCount += 1;
        return HttpResponse.json({ suggestions: ["Q1?", "Q2?", "Q3?", "Q4?"] });
      }),
    );

    const user = userEvent.setup();
    const onDismiss = vi.fn();
    renderWithClient(
      <SuggestionsPopover workspaceId="ws1" passage={PASSAGE} viewport={VIEWPORT} onDismiss={onDismiss} />,
    );

    await waitFor(() => expect(screen.getByText("Q1?")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /dismiss/i }));

    expect(onDismiss).toHaveBeenCalled();
    expect(callCount).toBe(1);
  });
});

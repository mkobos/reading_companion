import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { DiscussionPanel } from "../../src/discussion/DiscussionPanel";
import { server } from "../msw/server";

const VIEWPORT = { first_block_id: "000000", last_block_id: "000001" };

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("DiscussionPanel", () => {
  it("starts a discussion, then supports a follow-up turn in the thread view", async () => {
    const user = userEvent.setup();

    server.use(
      http.get("/api/workspaces/ws1/discussions", () => HttpResponse.json([])),
      http.post("/api/workspaces/ws1/discussions", () =>
        HttpResponse.json(
          {
            discussion_id: "d1",
            created_at: "2026-01-01T00:00:00Z",
            turns: [
              {
                turn_id: "t1",
                user_message: "What is this about?",
                agent_response: "It's about testing.",
                viewport: VIEWPORT,
                created_at: "2026-01-01T00:00:01Z",
              },
            ],
          },
          { status: 201 },
        ),
      ),
    );

    renderWithClient(<DiscussionPanel workspaceId="ws1" viewport={VIEWPORT} />);

    expect(await screen.findByText(/no discussions/i)).toBeInTheDocument();

    const input = screen.getByRole("textbox");
    await user.type(input, "What is this about?");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText("It's about testing.")).toBeInTheDocument();

    server.use(
      http.post("/api/workspaces/ws1/discussions/d1/turns", () =>
        HttpResponse.json(
          {
            turn_id: "t2",
            user_message: "Tell me more",
            agent_response: "Here is more detail.",
            viewport: VIEWPORT,
            created_at: "2026-01-01T00:00:02Z",
          },
          { status: 201 },
        ),
      ),
    );

    const followUpInput = screen.getAllByRole("textbox")[0]!;
    await user.type(followUpInput, "Tell me more");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(screen.getByText("Here is more detail.")).toBeInTheDocument());
    expect(screen.getByText("It's about testing.")).toBeInTheDocument();
  });

  it("expands an anchored discussion in place at its box, keeping other anchored boxes visible", async () => {
    const user = userEvent.setup();
    const anchor1 = {
      first_block_id: "000000",
      first_block_offset: 0,
      last_block_id: "000000",
      last_block_offset: 5,
      text: "Clause 4",
    };
    const anchor2 = {
      first_block_id: "000001",
      first_block_offset: 0,
      last_block_id: "000001",
      last_block_offset: 5,
      text: "Clause 9",
    };

    server.use(
      http.get("/api/workspaces/ws1/discussions", () =>
        HttpResponse.json([
          { discussion_id: "d1", anchor: anchor1, created_at: "2026-01-01T00:00:00Z", turn_count: 1 },
          { discussion_id: "d2", anchor: anchor2, created_at: "2026-01-02T00:00:00Z", turn_count: 0 },
        ]),
      ),
      http.get("/api/workspaces/ws1/discussions/d1", () =>
        HttpResponse.json({
          discussion_id: "d1",
          created_at: "2026-01-01T00:00:00Z",
          turns: [
            {
              turn_id: "t1",
              user_message: "What does clause 4 mean?",
              agent_response: "It means X.",
              viewport: VIEWPORT,
              created_at: "2026-01-01T00:00:01Z",
            },
          ],
        }),
      ),
    );

    renderWithClient(<DiscussionPanel workspaceId="ws1" viewport={VIEWPORT} />);

    const box1 = await screen.findByTestId("discussion-box-d1");
    await user.click(within(box1).getByRole("button"));

    expect(await within(box1).findByText("It means X.")).toBeInTheDocument();
    expect(screen.getByTestId("discussion-box-d2")).toBeInTheDocument();
  });
});

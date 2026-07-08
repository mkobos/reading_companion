import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useCreateDiscussion, useDiscussion, usePostTurn } from "../../src/api/queries";
import { server } from "../msw/server";

const VIEWPORT = { first_block_id: "000000", last_block_id: "000001" };

function makeWrapper(client: QueryClient) {
  return function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("discussion mutation hooks", () => {
  it("useCreateDiscussion seeds the discussion cache and invalidates the discussions list", async () => {
    server.use(
      http.post("/api/workspaces/ws1/discussions", () =>
        HttpResponse.json(
          { discussion_id: "d1", created_at: "2026-01-01T00:00:00Z", turns: [] },
          { status: 201 },
        ),
      ),
    );

    const client = new QueryClient();
    const invalidateSpy = client.invalidateQueries.bind(client);
    let invalidatedKey: unknown;
    client.invalidateQueries = ((opts: { queryKey: unknown }) => {
      invalidatedKey = opts.queryKey;
      return invalidateSpy(opts);
    }) as typeof client.invalidateQueries;

    const { result } = renderHook(() => useCreateDiscussion("ws1"), { wrapper: makeWrapper(client) });
    result.current.mutate({ message: "hi", viewport: VIEWPORT });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(client.getQueryData(["discussion", "ws1", "d1"])).toEqual({
      discussion_id: "d1",
      created_at: "2026-01-01T00:00:00Z",
      turns: [],
    });
    expect(invalidatedKey).toEqual(["discussions", "ws1"]);
  });

  it("usePostTurn appends the turn to the existing discussion cache entry", async () => {
    server.use(
      http.post("/api/workspaces/ws1/discussions/d1/turns", () =>
        HttpResponse.json(
          {
            turn_id: "t2",
            user_message: "follow up",
            agent_response: "reply",
            viewport: VIEWPORT,
            created_at: "2026-01-01T00:00:00Z",
          },
          { status: 201 },
        ),
      ),
    );

    const client = new QueryClient();
    client.setQueryData(["discussion", "ws1", "d1"], {
      discussion_id: "d1",
      created_at: "2026-01-01T00:00:00Z",
      turns: [
        {
          turn_id: "t1",
          user_message: "hi",
          agent_response: "hello",
          viewport: VIEWPORT,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
    });

    const { result } = renderHook(() => usePostTurn("ws1", "d1"), { wrapper: makeWrapper(client) });
    result.current.mutate({ message: "follow up", viewport: VIEWPORT });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const updated = client.getQueryData<{ turns: { turn_id: string }[] }>(["discussion", "ws1", "d1"]);
    expect(updated?.turns.map((t) => t.turn_id)).toEqual(["t1", "t2"]);
  });

  it("useDiscussion is enabled only when both ids are defined", () => {
    const client = new QueryClient();
    const { result } = renderHook(() => useDiscussion("ws1", undefined), { wrapper: makeWrapper(client) });
    expect(result.current.fetchStatus).toBe("idle");
  });

  describe("no retry-storm on 502", () => {
    it("useCreateDiscussion issues exactly one request on a 502", async () => {
      let callCount = 0;
      server.use(
        http.post("/api/workspaces/ws1/discussions", () => {
          callCount += 1;
          return HttpResponse.json({ message: "agent failed" }, { status: 502 });
        }),
      );

      const client = new QueryClient();
      const { result } = renderHook(() => useCreateDiscussion("ws1"), { wrapper: makeWrapper(client) });
      result.current.mutate({ message: "hi", viewport: VIEWPORT });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(callCount).toBe(1);
    });

    it("usePostTurn issues exactly one request on a 502", async () => {
      let callCount = 0;
      server.use(
        http.post("/api/workspaces/ws1/discussions/d1/turns", () => {
          callCount += 1;
          return HttpResponse.json({ message: "agent failed" }, { status: 502 });
        }),
      );

      const client = new QueryClient();
      const { result } = renderHook(() => usePostTurn("ws1", "d1"), { wrapper: makeWrapper(client) });
      result.current.mutate({ message: "hi", viewport: VIEWPORT });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(callCount).toBe(1);
    });
  });
});

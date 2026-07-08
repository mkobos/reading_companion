import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useGenerateJournal, useJournal } from "../../src/api/queries";
import { server } from "../msw/server";

function makeWrapper(client: QueryClient) {
  return function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("journal hooks", () => {
  it("useJournal resolves to undefined (not isError) on a 404 — 'no journal yet', never a hard error", async () => {
    server.use(http.get("/api/workspaces/ws1/journal", () => new HttpResponse(null, { status: 404 })));
    const client = new QueryClient();
    const { result } = renderHook(() => useJournal("ws1"), { wrapper: makeWrapper(client) });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeUndefined();
    expect(result.current.isError).toBe(false);
  });

  it("useGenerateJournal seeds the journal cache on success", async () => {
    server.use(
      http.post("/api/workspaces/ws1/journal", () =>
        HttpResponse.json({ text: "New journal", generated_at: "2026-01-01T00:00:00Z" }),
      ),
    );
    const client = new QueryClient();
    const { result } = renderHook(() => useGenerateJournal("ws1"), { wrapper: makeWrapper(client) });
    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(client.getQueryData(["journal", "ws1"])).toEqual({
      text: "New journal",
      generated_at: "2026-01-01T00:00:00Z",
    });
  });

  it("useGenerateJournal leaves the previous journal cache entry untouched on failure", async () => {
    server.use(http.post("/api/workspaces/ws1/journal", () => new HttpResponse(null, { status: 503 })));
    const client = new QueryClient();
    client.setQueryData(["journal", "ws1"], { text: "Old", generated_at: "2026-01-01T00:00:00Z" });
    const { result } = renderHook(() => useGenerateJournal("ws1"), { wrapper: makeWrapper(client) });
    result.current.mutate();

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(client.getQueryData(["journal", "ws1"])).toEqual({ text: "Old", generated_at: "2026-01-01T00:00:00Z" });
  });
});

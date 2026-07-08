import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useCreateNote, useDeleteNote, useNotes, useUpdateNote } from "../../src/api/queries";
import { server } from "../msw/server";

const ANCHOR = {
  first_block_id: "000000",
  first_block_offset: 0,
  last_block_id: "000000",
  last_block_offset: 5,
  text: "hello",
};

function makeWrapper(client: QueryClient) {
  return function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("note mutation hooks", () => {
  it("useCreateNote appends the created note to the notes list cache", async () => {
    server.use(
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

    const client = new QueryClient();
    client.setQueryData(["notes", "ws1"], []);
    const { result } = renderHook(() => useCreateNote("ws1"), { wrapper: makeWrapper(client) });
    result.current.mutate({ anchor: ANCHOR, text: "hi" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(client.getQueryData(["notes", "ws1"])).toEqual([
      {
        note_id: "n1",
        anchor: ANCHOR,
        text: "hi",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ]);
  });

  it("useUpdateNote replaces the matching note in the cache", async () => {
    server.use(
      http.put("/api/workspaces/ws1/notes/n1", () =>
        HttpResponse.json({
          note_id: "n1",
          anchor: ANCHOR,
          text: "updated",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-02T00:00:00Z",
        }),
      ),
    );

    const client = new QueryClient();
    client.setQueryData(["notes", "ws1"], [
      {
        note_id: "n1",
        anchor: ANCHOR,
        text: "hi",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ]);
    const { result } = renderHook(() => useUpdateNote("ws1"), { wrapper: makeWrapper(client) });
    result.current.mutate({ noteId: "n1", text: "updated" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(client.getQueryData<{ text: string }[]>(["notes", "ws1"])?.[0]?.text).toBe("updated");
  });

  it("useDeleteNote removes the note from the cache", async () => {
    server.use(http.delete("/api/workspaces/ws1/notes/n1", () => new HttpResponse(null, { status: 204 })));

    const client = new QueryClient();
    client.setQueryData(["notes", "ws1"], [
      {
        note_id: "n1",
        anchor: ANCHOR,
        text: "hi",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ]);
    const { result } = renderHook(() => useDeleteNote("ws1"), { wrapper: makeWrapper(client) });
    result.current.mutate("n1");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(client.getQueryData(["notes", "ws1"])).toEqual([]);
  });

  it("useNotes is enabled only when workspaceId is defined", () => {
    const client = new QueryClient();
    const { result } = renderHook(() => useNotes(undefined), { wrapper: makeWrapper(client) });
    expect(result.current.fetchStatus).toBe("idle");
  });
});

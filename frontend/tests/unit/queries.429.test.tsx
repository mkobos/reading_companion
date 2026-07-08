import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useCreateNote, useCreateWorkspace, useUploadDocument } from "../../src/api/queries";
import { server } from "../msw/server";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient();
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("mutation hooks never retry on 429 (no retry-storm)", () => {
  it("useCreateWorkspace issues exactly one request on a 429", async () => {
    let callCount = 0;
    server.use(
      http.post("/api/workspaces", () => {
        callCount += 1;
        return HttpResponse.json({ message: "rate limited" }, { status: 429, headers: { "Retry-After": "5" } });
      }),
    );

    const { result } = renderHook(() => useCreateWorkspace(), { wrapper });
    result.current.mutate();

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(callCount).toBe(1);
  });

  it("useUploadDocument issues exactly one request on a 429", async () => {
    let callCount = 0;
    server.use(
      http.post("/api/workspaces/ws1/document", () => {
        callCount += 1;
        return HttpResponse.json({ message: "rate limited" }, { status: 429, headers: { "Retry-After": "5" } });
      }),
    );

    const { result } = renderHook(() => useUploadDocument("ws1"), { wrapper });
    result.current.mutate(new File(["x"], "a.txt"));

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(callCount).toBe(1);
  });

  it("useCreateNote issues exactly one request on a 429", async () => {
    let callCount = 0;
    server.use(
      http.post("/api/workspaces/ws1/notes", () => {
        callCount += 1;
        return HttpResponse.json({ message: "rate limited" }, { status: 429, headers: { "Retry-After": "5" } });
      }),
    );

    const { result } = renderHook(() => useCreateNote("ws1"), { wrapper });
    result.current.mutate({
      anchor: {
        first_block_id: "000000",
        first_block_offset: 0,
        last_block_id: "000000",
        last_block_offset: 5,
        text: "hello",
      },
      text: "hi",
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(callCount).toBe(1);
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReadingView } from "../../src/document/ReadingView";
import { server } from "../msw/server";

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

type ObserverCallback = (entries: Partial<IntersectionObserverEntry>[]) => void;

// jsdom has no real IntersectionObserver; this fake auto-fires every
// observed element as intersecting so useViewportTracker settles a
// viewport, mirroring useViewportTracker.test.tsx's mocking approach.
class AutoIntersectingObserver implements IntersectionObserver {
  readonly root = null;
  readonly rootMargin = "";
  readonly thresholds: ReadonlyArray<number> = [];
  private readonly callback: ObserverCallback;
  constructor(callback: ObserverCallback) {
    this.callback = callback;
  }
  observe(el: Element) {
    this.callback([{ isIntersecting: true, target: el }]);
  }
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

describe("ReadingView onViewportChange", () => {
  beforeEach(() => {
    vi.stubGlobal("IntersectionObserver", AutoIntersectingObserver);
  });

  it("calls onViewportChange with the tracked viewport once a block becomes visible", async () => {
    server.use(
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

    const onViewportChange = vi.fn();
    renderWithClient(<ReadingView workspaceId="ws1" onViewportChange={onViewportChange} />);

    await screen.findByText("content");

    await waitFor(() =>
      expect(onViewportChange).toHaveBeenCalledWith({
        first_block_id: "000000",
        last_block_id: "000000",
      }),
    );
  });
});

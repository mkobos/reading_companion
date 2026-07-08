import { act, render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useViewportTracker } from "../../src/document/useViewportTracker";

type ObserverCallback = (entries: Partial<IntersectionObserverEntry>[]) => void;

let observedCallback: ObserverCallback | undefined;
let observedElements: Element[] = [];

class FakeIntersectionObserver implements IntersectionObserver {
  readonly root = null;
  readonly rootMargin = "";
  readonly thresholds: ReadonlyArray<number> = [];
  constructor(callback: ObserverCallback) {
    observedCallback = callback;
  }
  observe(el: Element) {
    observedElements.push(el);
  }
  unobserve(el: Element) {
    observedElements = observedElements.filter((e) => e !== el);
  }
  disconnect() {
    observedElements = [];
  }
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

function TestHarness({ onViewport }: { onViewport: (v: unknown) => void }) {
  const { containerRef, viewport } = useViewportTracker({ debounceMs: 10 });
  onViewport(viewport);
  return (
    <div ref={containerRef}>
      <p data-block-id="000000">a</p>
      <p data-block-id="000001">b</p>
      <p data-block-id="000002">c</p>
    </div>
  );
}

describe("useViewportTracker", () => {
  beforeEach(() => {
    observedCallback = undefined;
    observedElements = [];
    vi.stubGlobal("IntersectionObserver", FakeIntersectionObserver);
    vi.useFakeTimers();
  });

  it("starts with no tracked viewport", () => {
    const viewports: unknown[] = [];
    render(<TestHarness onViewport={(v) => viewports.push(v)} />);
    expect(viewports[0]).toBeUndefined();
  });

  it("updates to the first/last visible block ids after intersection changes settle (debounced)", async () => {
    const viewports: unknown[] = [];
    render(<TestHarness onViewport={(v) => viewports.push(v)} />);

    act(() => {
      observedCallback?.([
        { isIntersecting: true, target: observedElements[0] },
        { isIntersecting: true, target: observedElements[1] },
        { isIntersecting: false, target: observedElements[2] },
      ] as IntersectionObserverEntry[]);
    });

    act(() => {
      vi.advanceTimersByTime(10);
    });

    expect(viewports.at(-1)).toEqual({ first_block_id: "000000", last_block_id: "000001" });
    vi.useRealTimers();
  });
});

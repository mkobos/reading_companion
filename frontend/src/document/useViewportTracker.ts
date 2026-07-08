import { useEffect, useRef, useState } from "react";
import { debounce } from "../lib/debounce";

export interface TrackedViewport {
  first_block_id: string;
  last_block_id: string;
}

/** Tracks which rendered blocks are currently visible in the scroll
 * container via IntersectionObserver, exposing the debounced
 * {first_block_id, last_block_id} range. Phase 1 exposes this as
 * observable state only — it is not yet sent in any request (plan §4). */
export function useViewportTracker(options: { debounceMs?: number } = {}) {
  const { debounceMs = 200 } = options;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [viewport, setViewport] = useState<TrackedViewport | undefined>(undefined);
  const visibleIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const commit = debounce(() => {
      const ids = Array.from(visibleIdsRef.current).sort();
      setViewport(
        ids.length === 0
          ? undefined
          : { first_block_id: ids[0]!, last_block_id: ids[ids.length - 1]! },
      );
    }, debounceMs);

    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const blockId = (entry.target as HTMLElement).dataset.blockId;
        if (!blockId) continue;
        if (entry.isIntersecting) {
          visibleIdsRef.current.add(blockId);
        } else {
          visibleIdsRef.current.delete(blockId);
        }
      }
      commit();
    });

    const targets = container.querySelectorAll<HTMLElement>("[data-block-id]");
    targets.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [debounceMs]);

  return { containerRef, viewport };
}

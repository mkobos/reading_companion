import { useLayoutEffect, useRef, useState } from "react";

/** Vertical gap (px) enforced between two stacked anchored boxes. */
const GAP_PX = 8;

export interface AnchoredItem {
  id: string;
  blockId: string;
}

export interface AnchoredBox {
  id: string;
  /** Raw top (px), relative to the positioning column's own top edge —
   * i.e. `blockEl.getBoundingClientRect().top - columnEl.getBoundingClientRect().top`. */
  top: number;
  height: number;
}

/** Google-Docs-margin-comments-style collision avoidance: boxes are kept
 * as close as possible to their own anchor's raw top, but never above the
 * column's own top edge (clamped to 0), and never overlapping the box
 * above them (pushed down by exactly the overlap amount, cascading
 * through consecutive overlaps). A single top-to-bottom pass over boxes
 * sorted by raw top — not a full layout solver — since boxes are only
 * ever pushed down, never sideways or up. */
export function resolveCollisions(boxes: AnchoredBox[]): Map<string, number> {
  const sorted = [...boxes].sort((a, b) => a.top - b.top);
  const result = new Map<string, number>();
  let prevBottom: number | undefined;

  for (const box of sorted) {
    const minTop = prevBottom === undefined ? 0 : prevBottom + GAP_PX;
    const top = Math.max(box.top, minTop);
    result.set(box.id, top);
    prevBottom = top + box.height;
  }

  return result;
}

/** Positions a set of boxes (e.g. discussion cards in the right margin) at
 * the page height of their anchor blocks (e.g. paragraphs in the left
 * reading column) — even though the boxes and their anchor blocks live in
 * separate DOM subtrees. Measures both subtrees' rects relative to a
 * shared `columnRef` wrapper, then runs `resolveCollisions` so boxes never
 * overlap. Consumers attach `columnRef` to the positioning wrapper and,
 * for each item, a ref via `boxRefs.current.set(item.id, el)` on that
 * item's box element. */
export function useAnchoredBoxPositions(readingContainer: HTMLElement | null, items: AnchoredItem[]) {
  const columnRef = useRef<HTMLDivElement | null>(null);
  const boxRefs = useRef(new Map<string, HTMLElement | null>());
  const [tops, setTops] = useState<Map<string, number>>(new Map());
  const [minHeight, setMinHeight] = useState<number | undefined>(undefined);
  const [ready, setReady] = useState(false);

  useLayoutEffect(() => {
    const column = columnRef.current;
    if (items.length === 0) {
      setReady(true);
      return;
    }
    if (!readingContainer || !column) return;

    const recompute = () => {
      const columnTop = column.getBoundingClientRect().top;
      const rawBoxes: AnchoredBox[] = [];
      for (const item of items) {
        const blockEl = readingContainer.querySelector<HTMLElement>(
          `[data-block-id="${CSS.escape(item.blockId)}"]`,
        );
        const boxEl = boxRefs.current.get(item.id);
        if (!blockEl || !boxEl) continue;
        rawBoxes.push({
          id: item.id,
          top: blockEl.getBoundingClientRect().top - columnTop,
          height: boxEl.offsetHeight,
        });
      }

      const resolved = resolveCollisions(rawBoxes);
      setTops(resolved);

      const bottoms = rawBoxes.map((box) => (resolved.get(box.id) ?? box.top) + box.height);
      setMinHeight(Math.max(readingContainer.offsetHeight, ...bottoms, 0));
      setReady(true);
    };

    recompute();
    window.addEventListener("resize", recompute);
    return () => window.removeEventListener("resize", recompute);
  }, [readingContainer, items]);

  return { columnRef, boxRefs, tops, minHeight, ready };
}

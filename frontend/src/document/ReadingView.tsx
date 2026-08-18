import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import { useDocument } from "../api/queries";
import type { components } from "../api/types";
import { NoteIndicator } from "../note/NoteIndicator";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { Block } from "./Block";
import { buildHighlightRanges } from "./buildHighlightRanges";
import { passageFromSelection } from "./passageFromSelection";
import { SuggestionsPopover } from "./SuggestionsPopover";
import { useViewportTracker, type TrackedViewport } from "./useViewportTracker";

type Note = components["schemas"]["Note"];
type Passage = components["schemas"]["Passage"];

interface ReadingViewProps {
  workspaceId: string;
  /** Notified with the debounced tracked viewport on every change (Phase 2:
   * threads the visible range into the discussion panel). */
  onViewportChange?: (viewport: TrackedViewport | undefined) => void;
  /** Notified whenever the reading container DOM node becomes available (or
   * changes), so a parent can measure it (e.g. to align discussion boxes
   * in a sibling column to their anchor's height). */
  onContainerChange?: (container: HTMLElement | null) => void;
  /** Existing notes to anchor NoteIndicators next to their last block. */
  notes?: Note[];
  onSelectNote?: (noteId: string) => void;
  /** The currently marked (ephemeral) passage, controlled by the parent —
   * mirrors the viewport pattern, but the parent (not ReadingView) owns the
   * source of truth so it can also be cleared from the Notes tab. */
  markedPassage?: Passage;
  onPassageMarked?: (passage: Passage | undefined) => void;
  onDiscussionStarted?: () => void;
  /** The passage to visually highlight (e.g. the anchor of a discussion
   * whose box was just clicked), or undefined for no highlight. */
  highlightedPassage?: Passage;
}

/** Renders a workspace's document as an ordered list of blocks, tracks the
 * visible viewport range as the reader scrolls (plan §4), renders inline
 * NoteIndicators for existing notes, and derives a Passage from the current
 * text selection on mouseup so a SuggestionsPopover can be shown. */
export function ReadingView({
  workspaceId,
  onViewportChange,
  onContainerChange,
  notes,
  onSelectNote,
  markedPassage,
  onPassageMarked,
  onDiscussionStarted,
  highlightedPassage,
}: ReadingViewProps) {
  const { data, isPending, isError, error } = useDocument(workspaceId);
  const { containerRef, container, viewport } = useViewportTracker();
  const [markTopOffset, setMarkTopOffset] = useState<number | undefined>(undefined);

  useEffect(() => {
    onViewportChange?.(viewport);
  }, [viewport, onViewportChange]);

  useEffect(() => {
    onContainerChange?.(container);
  }, [container, onContainerChange]);

  const highlightRanges = useMemo(
    () => (highlightedPassage && data ? buildHighlightRanges(highlightedPassage, data.blocks) : undefined),
    [highlightedPassage, data],
  );

  useLayoutEffect(() => {
    if (!markedPassage) {
      setMarkTopOffset(undefined);
      return;
    }
    if (!container) return;
    const updatePosition = () => {
      const el = container.querySelector<HTMLElement>(
        `[data-block-id="${CSS.escape(markedPassage.first_block_id)}"]`,
      );
      setMarkTopOffset(el?.offsetTop);
    };
    updatePosition();
    window.addEventListener("resize", updatePosition);
    return () => window.removeEventListener("resize", updatePosition);
  }, [markedPassage, container]);

  const handleMouseUp = () => {
    if (!data || !onPassageMarked) return;
    const passage = passageFromSelection(window.getSelection(), data.blocks);
    onPassageMarked(passage);
  };

  if (isPending) return <LoadingState label="Loading document…" />;
  if (isError) {
    return <ErrorNotice message={error instanceof Error ? error.message : "Failed to load document."} />;
  }

  const notesByLastBlockId = new Map<string, Note[]>();
  for (const note of notes ?? []) {
    const existing = notesByLastBlockId.get(note.anchor.last_block_id);
    if (existing) {
      existing.push(note);
    } else {
      notesByLastBlockId.set(note.anchor.last_block_id, [note]);
    }
  }

  return (
    <div
      ref={containerRef}
      data-testid="reading-view"
      data-first-block-id={viewport?.first_block_id}
      data-last-block-id={viewport?.last_block_id}
      onMouseUp={handleMouseUp}
      className="relative mx-auto max-w-2xl space-y-4 p-6"
    >
      {data.blocks.map((block) => (
        <span key={block.block_id} className="block">
          <Block block={block} highlight={highlightRanges?.get(block.block_id)} />
          {notesByLastBlockId.get(block.block_id)?.map((note) => (
            <NoteIndicator key={note.note_id} note={note} onSelect={(id) => onSelectNote?.(id)} />
          ))}
        </span>
      ))}
      {markedPassage && (
        <div
          className="mt-4 md:absolute md:left-full md:top-0 md:z-20 md:mt-0 md:ml-4 md:w-72"
          style={markTopOffset !== undefined ? { top: markTopOffset } : undefined}
          // Now a DOM descendant of the container (so it can be positioned
          // relative to it) — without this, clicks inside it would bubble up
          // to handleMouseUp, which reads the (by-then collapsed) selection
          // and clears markedPassage before the click's own handler runs.
          onMouseUp={(event) => event.stopPropagation()}
        >
          <SuggestionsPopover
            workspaceId={workspaceId}
            passage={markedPassage}
            viewport={viewport}
            onDismiss={() => onPassageMarked?.(undefined)}
            onDiscussionStarted={onDiscussionStarted}
          />
        </div>
      )}
    </div>
  );
}

import { useEffect } from "react";
import { useDocument } from "../api/queries";
import type { components } from "../api/types";
import { NoteIndicator } from "../note/NoteIndicator";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { Block } from "./Block";
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
  /** Existing notes to anchor NoteIndicators next to their last block. */
  notes?: Note[];
  onSelectNote?: (noteId: string) => void;
  /** The currently marked (ephemeral) passage, controlled by the parent —
   * mirrors the viewport pattern, but the parent (not ReadingView) owns the
   * source of truth so it can also be cleared from the Notes tab. */
  markedPassage?: Passage;
  onPassageMarked?: (passage: Passage | undefined) => void;
  onDiscussionStarted?: () => void;
}

/** Renders a workspace's document as an ordered list of blocks, tracks the
 * visible viewport range as the reader scrolls (plan §4), renders inline
 * NoteIndicators for existing notes, and derives a Passage from the current
 * text selection on mouseup so a SuggestionsPopover can be shown. */
export function ReadingView({
  workspaceId,
  onViewportChange,
  notes,
  onSelectNote,
  markedPassage,
  onPassageMarked,
  onDiscussionStarted,
}: ReadingViewProps) {
  const { data, isPending, isError, error } = useDocument(workspaceId);
  const { containerRef, viewport } = useViewportTracker();

  useEffect(() => {
    onViewportChange?.(viewport);
  }, [viewport, onViewportChange]);

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
    <div className="space-y-3">
      <div
        ref={containerRef}
        data-testid="reading-view"
        data-first-block-id={viewport?.first_block_id}
        data-last-block-id={viewport?.last_block_id}
        onMouseUp={handleMouseUp}
        className="mx-auto max-w-2xl space-y-4 p-6"
      >
        {data.blocks.map((block) => (
          <span key={block.block_id} className="block">
            <Block block={block} />
            {notesByLastBlockId.get(block.block_id)?.map((note) => (
              <NoteIndicator key={note.note_id} note={note} onSelect={(id) => onSelectNote?.(id)} />
            ))}
          </span>
        ))}
      </div>
      {markedPassage && (
        <SuggestionsPopover
          workspaceId={workspaceId}
          passage={markedPassage}
          viewport={viewport}
          onDismiss={() => onPassageMarked?.(undefined)}
          onDiscussionStarted={onDiscussionStarted}
        />
      )}
    </div>
  );
}

import { useState } from "react";
import { useNotes } from "../api/queries";
import type { components } from "../api/types";
import { DiscussionPanel } from "../discussion/DiscussionPanel";
import { ReadingView } from "../document/ReadingView";
import type { TrackedViewport } from "../document/useViewportTracker";
import { JournalTab } from "../journal/JournalTab";
import { NotesTab } from "../note/NotesTab";

type Passage = components["schemas"]["Passage"];
type RightTab = "discussions" | "notes" | "journal";

const TABS: { id: RightTab; label: string }[] = [
  { id: "discussions", label: "Discussions" },
  { id: "notes", label: "Notes" },
  { id: "journal", label: "Journal" },
];

/** Two-column shell for the has_document branch: the reading view on the
 * left, a tabbed Discussions | Notes | Journal panel on the right (plan §4,
 * Phase 3). markedPassage is lifted here so both ReadingView (which renders
 * the ephemeral SuggestionsPopover) and NotesTab (which anchors a new note
 * to it) share the same mark. */
export function DocumentWorkspace({ workspaceId }: { workspaceId: string }) {
  const [viewport, setViewport] = useState<TrackedViewport | undefined>(undefined);
  const [markedPassage, setMarkedPassage] = useState<Passage | undefined>(undefined);
  const [highlightedPassage, setHighlightedPassage] = useState<Passage | undefined>(undefined);
  const [readingContainer, setReadingContainer] = useState<HTMLElement | null>(null);
  const [rightTab, setRightTab] = useState<RightTab>("discussions");
  const { data: notes } = useNotes(workspaceId);

  const selectRightTab = (tab: RightTab) => {
    if (tab !== "discussions") setHighlightedPassage(undefined);
    setRightTab(tab);
  };

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <div className="md:w-1/2">
        <ReadingView
          workspaceId={workspaceId}
          onViewportChange={setViewport}
          onContainerChange={setReadingContainer}
          notes={notes}
          onSelectNote={() => selectRightTab("notes")}
          markedPassage={markedPassage}
          onPassageMarked={setMarkedPassage}
          onDiscussionStarted={() => selectRightTab("discussions")}
          highlightedPassage={highlightedPassage}
        />
      </div>
      <div className="space-y-3 md:w-1/2">
        <div role="tablist" className="flex gap-2 border-b">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={rightTab === tab.id}
              onClick={() => selectRightTab(tab.id)}
              className={`px-3 py-1 text-sm ${rightTab === tab.id ? "border-b-2 border-black font-medium" : ""}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {rightTab === "discussions" && (
          <DiscussionPanel
            workspaceId={workspaceId}
            viewport={viewport}
            readingContainer={readingContainer}
            onHighlightPassage={setHighlightedPassage}
          />
        )}
        {rightTab === "notes" && (
          <NotesTab
            workspaceId={workspaceId}
            markedPassage={markedPassage}
            onMarkHandled={() => setMarkedPassage(undefined)}
          />
        )}
        {rightTab === "journal" && <JournalTab workspaceId={workspaceId} />}
      </div>
    </div>
  );
}

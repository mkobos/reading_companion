import { useState } from "react";
import { useGenerateJournal, useJournal } from "../api/queries";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { JournalMarkdown } from "./JournalMarkdown";
import { mapJournalError } from "./mapJournalError";

/** Reading journal tab: a GET 404 means "no journal yet" (CTA, not an error
 * banner); generation/regeneration is strictly user-button-driven; on
 * failure the previous journal (if any), already in the query cache, stays
 * visible unmodified — only the mutation's own error is shown alongside it. */
export function JournalTab({ workspaceId }: { workspaceId: string }) {
  const { data: journal, isPending, isError, error } = useJournal(workspaceId);
  const generate = useGenerateJournal(workspaceId);
  const [generateError, setGenerateError] = useState<string | undefined>(undefined);

  const handleGenerate = () => {
    setGenerateError(undefined);
    generate.mutate(undefined, { onError: (err) => setGenerateError(mapJournalError(err)) });
  };

  const buttonLabel = journal
    ? generate.isPending
      ? "Regenerating…"
      : "Regenerate journal"
    : generate.isPending
      ? "Generating…"
      : "Generate a reading journal";

  return (
    <div className="space-y-3">
      {isPending && <LoadingState label="Loading journal…" />}
      {isError && (
        <ErrorNotice message={error instanceof Error ? error.message : "Failed to load journal."} />
      )}
      {generateError && <ErrorNotice message={generateError} />}

      {journal && <JournalMarkdown text={journal.text} />}
      {!journal && !isPending && <p className="text-sm text-gray-500">No reading journal yet.</p>}

      {!isPending && (
        <button
          type="button"
          onClick={handleGenerate}
          disabled={generate.isPending}
          className="rounded border px-3 py-1 text-sm"
        >
          {buttonLabel}
        </button>
      )}
    </div>
  );
}

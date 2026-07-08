import { useId, useState } from "react";
import { useUploadDocument } from "../api/queries";
import { ApiError } from "../lib/errors";
import type { components } from "../api/types";
import { ErrorNotice } from "../ui/ErrorNotice";

type DocumentView = components["schemas"]["DocumentView"];

const ACCEPTED_EXTENSIONS = [".txt", ".md"];
// UX-only guard, not a security boundary — the backend's 400/413/415 are
// the authoritative validation (Phase 1 plan §6.2).
const MAX_CLIENT_SIDE_BYTES = 2_000_000;

function clientPreCheckError(file: File): string | undefined {
  const hasAcceptedExtension = ACCEPTED_EXTENSIONS.some((ext) =>
    file.name.toLowerCase().endsWith(ext),
  );
  if (!hasAcceptedExtension) {
    return "Only .txt and .md files are accepted.";
  }
  if (file.size > MAX_CLIENT_SIDE_BYTES) {
    return "File is too large.";
  }
  return undefined;
}

export function UploadPanel({
  workspaceId,
  onUploaded,
}: {
  workspaceId: string;
  onUploaded: (document: DocumentView) => void;
}) {
  const inputId = useId();
  const [clientError, setClientError] = useState<string | undefined>(undefined);
  const upload = useUploadDocument(workspaceId);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    const precheckError = clientPreCheckError(file);
    if (precheckError) {
      setClientError(precheckError);
      return;
    }
    setClientError(undefined);
    upload.mutate(file, { onSuccess: onUploaded });
  };

  const errorMessage =
    clientError ??
    (upload.isError
      ? upload.error instanceof ApiError
        ? upload.error.message
        : "Upload failed."
      : undefined);

  return (
    <div className="mx-auto max-w-md space-y-4 p-6 text-center">
      <label htmlFor={inputId} className="block cursor-pointer font-medium">
        Upload a document (.txt or .md)
      </label>
      <input
        id={inputId}
        type="file"
        accept=".txt,.md"
        aria-label="Upload a document"
        onChange={handleChange}
        disabled={upload.isPending}
      />
      {upload.isPending && <p>Uploading…</p>}
      {errorMessage && <ErrorNotice message={errorMessage} />}
    </div>
  );
}

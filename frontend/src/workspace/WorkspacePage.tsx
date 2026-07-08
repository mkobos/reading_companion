import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useCreateWorkspace, useDeleteWorkspace, useWorkspace } from "../api/queries";
import { ApiError } from "../lib/errors";
import { ConfirmDialog } from "../ui/ConfirmDialog";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { ReadingView } from "../document/ReadingView";
import { UploadPanel } from "../document/UploadPanel";
import { NotFoundPage } from "./NotFoundPage";
import { clearLastWorkspace, setLastWorkspace } from "./workspaceCookie";

/** The workspace-scoped shell at /w/:workspaceId. Fetches WorkspaceDetail
 * and branches to the empty-state upload panel or the reading view; hosts
 * the "new workspace" and "delete" actions (plan §4). */
export function WorkspacePage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const { data, isPending, isError, error, refetch } = useWorkspace(workspaceId);
  const createWorkspace = useCreateWorkspace();
  const deleteWorkspace = useDeleteWorkspace();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [actionError, setActionError] = useState<string | undefined>(undefined);

  // Direct/shared URL access: possession of the URL grants access; set the
  // cookie to follow wherever the user actually is (plan §4, lifecycle 4).
  useEffect(() => {
    if (data && workspaceId) setLastWorkspace(workspaceId);
  }, [data, workspaceId]);

  if (!workspaceId) return <NotFoundPage />;
  if (isPending) return <LoadingState label="Loading workspace…" />;
  if (isError) {
    if (error instanceof ApiError && error.status === 404) return <NotFoundPage />;
    return <ErrorNotice message={error instanceof Error ? error.message : "Failed to load workspace."} />;
  }

  const handleNewWorkspace = () => {
    setActionError(undefined);
    createWorkspace.mutate(undefined, {
      onSuccess: (workspace) => {
        setLastWorkspace(workspace.workspace_id);
        navigate(`/w/${workspace.workspace_id}`);
      },
      onError: (err) => {
        setActionError(err instanceof ApiError ? err.message : "Could not create a new workspace.");
      },
    });
  };

  const handleDelete = () => {
    setConfirmingDelete(false);
    setActionError(undefined);
    deleteWorkspace.mutate(workspaceId, {
      onSuccess: () => {
        clearLastWorkspace();
        createWorkspace.mutate(undefined, {
          onSuccess: (workspace) => {
            setLastWorkspace(workspace.workspace_id);
            navigate(`/w/${workspace.workspace_id}`, { replace: true });
          },
          onError: (err) => {
            setActionError(err instanceof ApiError ? err.message : "Could not create a new workspace.");
          },
        });
      },
      onError: (err) => {
        setActionError(err instanceof ApiError ? err.message : "Could not delete this workspace.");
      },
    });
  };

  return (
    <div>
      <header className="flex justify-end gap-2 p-3">
        <button type="button" onClick={handleNewWorkspace} className="rounded border px-3 py-1 text-sm">
          New workspace
        </button>
        <button
          type="button"
          onClick={() => setConfirmingDelete(true)}
          className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
        >
          Delete workspace
        </button>
      </header>

      {actionError && <ErrorNotice message={actionError} />}

      {data.has_document ? (
        <ReadingView workspaceId={workspaceId} />
      ) : (
        <UploadPanel workspaceId={workspaceId} onUploaded={() => refetch()} />
      )}

      {confirmingDelete && (
        <ConfirmDialog
          title="Delete this workspace?"
          message="This permanently deletes the document and all workspace data. This cannot be undone."
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </div>
  );
}

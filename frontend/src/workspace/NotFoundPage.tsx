import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateWorkspace } from "../api/queries";
import { ApiError } from "../lib/errors";
import { ErrorNotice } from "../ui/ErrorNotice";
import { setLastWorkspace } from "./workspaceCookie";

/** Catch-all for unknown routes and the malformed/nonexistent workspace ID
 * case. Reveals nothing about whether the ID ever existed (plan §6.4/§6.7);
 * creates nothing until the user explicitly asks (plan §4/§7 lifecycle 8). */
export function NotFoundPage() {
  const navigate = useNavigate();
  const createWorkspace = useCreateWorkspace();
  const [error, setError] = useState<string | undefined>(undefined);

  const handleCreate = () => {
    setError(undefined);
    createWorkspace.mutate(undefined, {
      onSuccess: (workspace) => {
        setLastWorkspace(workspace.workspace_id);
        navigate(`/w/${workspace.workspace_id}`, { replace: true });
      },
      onError: (err) => {
        setError(err instanceof ApiError ? err.message : "Could not create a new workspace.");
      },
    });
  };

  return (
    <div className="mx-auto max-w-md space-y-4 p-6 text-center">
      <h1 className="text-xl font-semibold">Workspace not found</h1>
      <p>This workspace does not exist or is no longer available.</p>
      <button
        type="button"
        onClick={handleCreate}
        disabled={createWorkspace.isPending}
        className="rounded bg-gray-900 px-4 py-2 text-white"
      >
        Create a new workspace
      </button>
      {error && <ErrorNotice message={error} />}
    </div>
  );
}

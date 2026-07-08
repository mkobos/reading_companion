import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createWorkspace, getWorkspace } from "../api/workspaces";
import { ApiError } from "../lib/errors";
import { ErrorNotice } from "../ui/ErrorNotice";
import { LoadingState } from "../ui/LoadingState";
import { Toast } from "../ui/Toast";
import { clearLastWorkspace, getLastWorkspace, setLastWorkspace } from "./workspaceCookie";

/** How long the "your workspace is gone" notice stays visible before the
 * fresh workspace is created and redirected to. Without this, a fast local
 * backend can complete the whole recovery within a few milliseconds,
 * unmounting this component (and its toast) before a user could ever
 * actually read the notice. */
const DELETED_WORKSPACE_NOTICE_MS = 1500;

/** "/" logic (plan §4, lifecycle scenarios 1-3): if a last-used workspace
 * cookie exists and still resolves, redirect there. If it points at a
 * deleted/nonexistent workspace, clear it, show a transient notice, and
 * create a fresh one. If no cookie, create a fresh workspace. */
export function RootRedirect() {
  const navigate = useNavigate();
  const [toast, setToast] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const ranRef = useRef(false);

  useEffect(() => {
    // Guard against React 18 StrictMode's dev-only double-invocation of
    // effects. Deliberately no cleanup/cancellation here: a cleanup flag
    // would be set by StrictMode's synthetic mount->cleanup->remount cycle
    // and would incorrectly poison this same in-flight run before its
    // fetch resolves (ranRef only blocks a *second* run() call — it does
    // nothing to protect an already-started one from a phantom cleanup).
    // Letting the single guarded run() always complete and call navigate()
    // is safe even if this component happens to unmount for real, since
    // navigate/setState calls on an unmounted function component are
    // harmless no-ops in React 18.
    if (ranRef.current) return;
    ranRef.current = true;

    async function createFreshWorkspace() {
      try {
        const workspace = await createWorkspace();
        setLastWorkspace(workspace.workspace_id);
        navigate(`/w/${workspace.workspace_id}`, { replace: true });
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not create a workspace.");
      }
    }

    async function run() {
      const lastId = getLastWorkspace();
      if (!lastId) {
        await createFreshWorkspace();
        return;
      }

      try {
        await getWorkspace(lastId);
        navigate(`/w/${lastId}`, { replace: true });
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          clearLastWorkspace();
          setToast("Your last workspace is no longer available — creating a new one.");
          await new Promise((resolve) => setTimeout(resolve, DELETED_WORKSPACE_NOTICE_MS));
          await createFreshWorkspace();
        } else {
          setError(err instanceof ApiError ? err.message : "Could not load your workspace.");
        }
      }
    }

    void run();
  }, [navigate]);

  return (
    <>
      {toast && <Toast message={toast} />}
      {error ? <ErrorNotice message={error} /> : <LoadingState label="Setting up your workspace…" />}
    </>
  );
}

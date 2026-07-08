/** A transient, dismissible status message (e.g. "workspace not found,
 * created a new one"). Renders untrusted text as a text child only.
 * Uses role="alert" (assertive) rather than role="status" (polite,
 * used by LoadingState) so the two can be distinguished — both by
 * screen readers and by tests — when shown at the same time, e.g.
 * while a fresh workspace is being created after this notice. */
export function Toast({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  return (
    <div
      role="alert"
      className="fixed inset-x-0 top-4 mx-auto w-fit rounded bg-gray-900 px-4 py-2 text-white shadow"
    >
      <span>{message}</span>
      {onDismiss && (
        <button type="button" onClick={onDismiss} aria-label="Dismiss" className="ml-3 opacity-70">
          ×
        </button>
      )}
    </div>
  );
}

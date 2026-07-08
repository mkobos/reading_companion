export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  onConfirm,
  onCancel,
}: {
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div role="dialog" aria-modal="true" aria-label={title} className="fixed inset-0 flex items-center justify-center bg-black/40">
      <div className="max-w-sm space-y-4 rounded bg-white p-6 shadow-lg">
        <h2 className="font-semibold">{title}</h2>
        <p>{message}</p>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onCancel} className="rounded border px-3 py-1">
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded bg-red-600 px-3 py-1 text-white"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

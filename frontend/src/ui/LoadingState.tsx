export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" className="p-6 text-center text-gray-500">
      {label}
    </div>
  );
}

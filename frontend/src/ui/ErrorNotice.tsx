/** Renders a backend or client error message as plain text only — never
 * HTML. `message` may be untrusted server-provided text. */
export function ErrorNotice({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded border border-red-300 bg-red-50 p-3 text-red-800">
      {message}
    </div>
  );
}

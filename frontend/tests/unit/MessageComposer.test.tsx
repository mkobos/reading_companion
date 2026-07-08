import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MessageComposer } from "../../src/discussion/MessageComposer";
import { ApiError } from "../../src/lib/errors";

const VIEWPORT = { first_block_id: "000000", last_block_id: "000001" };

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("MessageComposer", () => {
  it("shows the pending indicator, disables input, and preserves text while onSend is in flight", async () => {
    const user = userEvent.setup();
    const { promise, resolve } = deferred<void>();
    const onSend = vi.fn().mockReturnValue(promise);

    render(<MessageComposer onSend={onSend} viewport={VIEWPORT} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "hello there");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByRole("status")).toBeInTheDocument();
    expect(input).toBeDisabled();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
    expect(input).toHaveValue("hello there");

    resolve();

    await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
  });

  it("clears the input on success and calls onSend with the typed message", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn().mockResolvedValue(undefined);

    render(<MessageComposer onSend={onSend} viewport={VIEWPORT} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "hello there");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(input).toHaveValue(""));
    expect(onSend).toHaveBeenCalledWith("hello there");
  });

  it("shows an error and Resend button on a 502, retains input, and retries with the same text", async () => {
    const user = userEvent.setup();
    const onSend = vi
      .fn()
      .mockRejectedValueOnce(new ApiError(502, "Agent turn failed; nothing was saved. Retry."))
      .mockResolvedValueOnce(undefined);

    render(<MessageComposer onSend={onSend} viewport={VIEWPORT} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "hello there");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/agent turn failed/i);
    expect(input).toHaveValue("hello there");

    const resendButton = screen.getByRole("button", { name: /resend/i });
    await user.click(resendButton);

    await waitFor(() => expect(input).toHaveValue(""));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(onSend).toHaveBeenNthCalledWith(2, "hello there");
  });

  it("shows the fixed connection-lost copy (not the raw error) on a plain network error, and resend works", async () => {
    const user = userEvent.setup();
    const onSend = vi
      .fn()
      .mockRejectedValueOnce(new Error("network fail"))
      .mockResolvedValueOnce(undefined);

    render(<MessageComposer onSend={onSend} viewport={VIEWPORT} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "hello there");
    await user.click(screen.getByRole("button", { name: /send/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(
      "Connection lost before the agent responded. Your message is still here — resend it.",
    );
    expect(screen.queryByText("network fail")).toBeNull();
    expect(input).toHaveValue("hello there");

    await user.click(screen.getByRole("button", { name: /resend/i }));

    await waitFor(() => expect(input).toHaveValue(""));
    expect(onSend).toHaveBeenNthCalledWith(2, "hello there");
  });

  it("disables the send control when viewport is undefined even with non-empty input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();

    render(<MessageComposer onSend={onSend} viewport={undefined} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "hello");

    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("disables the send control when input is empty or whitespace-only", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();

    render(<MessageComposer onSend={onSend} viewport={VIEWPORT} />);

    const input = screen.getByRole("textbox");
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();

    await user.type(input, "   ");
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });
});

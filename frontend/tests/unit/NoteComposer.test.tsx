import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "../../src/lib/errors";
import { NoteComposer } from "../../src/note/NoteComposer";

describe("NoteComposer", () => {
  it("rejects empty text client-side without calling onSave", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(<NoteComposer onSave={onSave} onCancel={() => {}} />);

    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/empty/i);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("rejects whitespace-only text client-side without calling onSave", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(<NoteComposer onSave={onSave} onCancel={() => {}} />);

    await user.type(screen.getByRole("textbox"), "   ");
    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/empty/i);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("calls onSave with the typed text", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<NoteComposer onSave={onSave} onCancel={() => {}} />);

    await user.type(screen.getByRole("textbox"), "my note");
    await user.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(onSave).toHaveBeenCalledWith("my note"));
  });

  it("shows a mapped error and keeps the composer open (with the text retained) on failure", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockRejectedValue(new ApiError(500, "boom"));
    render(<NoteComposer onSave={onSave} onCancel={() => {}} />);

    await user.type(screen.getByRole("textbox"), "my note");
    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("my note");
  });

  it("calls onCancel when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(<NoteComposer onSave={vi.fn()} onCancel={onCancel} />);
    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it("pre-fills initialText when provided (edit mode)", () => {
    render(<NoteComposer initialText="existing text" onSave={vi.fn()} onCancel={() => {}} />);
    expect(screen.getByRole("textbox")).toHaveValue("existing text");
  });
});

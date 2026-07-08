import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NoteIndicator } from "../../src/note/NoteIndicator";

const NOTE = {
  note_id: "n1",
  anchor: {
    first_block_id: "000000",
    first_block_offset: 0,
    last_block_id: "000000",
    last_block_offset: 5,
    text: "hello",
  },
  text: "note text",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("NoteIndicator", () => {
  it("calls onSelect with the note id when clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<NoteIndicator note={NOTE} onSelect={onSelect} />);
    await user.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith("n1");
  });
});

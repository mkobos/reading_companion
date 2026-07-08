import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DiscussionList } from "../../src/discussion/DiscussionList";

describe("DiscussionList", () => {
  it("shows an empty state when there are no discussions", () => {
    render(<DiscussionList discussions={[]} onSelect={() => {}} />);
    expect(screen.getByText(/no discussions/i)).toBeInTheDocument();
  });

  it("renders previews and turn counts, falling back to a placeholder when no preview exists", () => {
    render(
      <DiscussionList
        discussions={[
          {
            discussion_id: "d1",
            created_at: "2026-01-01T00:00:00Z",
            turn_count: 2,
            first_message_preview: "What does clause 4 mean?",
          },
          { discussion_id: "d2", created_at: "2026-01-02T00:00:00Z", turn_count: 0 },
        ]}
        onSelect={() => {}}
      />,
    );

    expect(screen.getByText("What does clause 4 mean?")).toBeInTheDocument();
    expect(screen.getByText(/new discussion/i)).toBeInTheDocument();
    expect(screen.getByText(/2 turns/)).toBeInTheDocument();
  });

  it("calls onSelect with the discussion_id when an item is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <DiscussionList
        discussions={[{ discussion_id: "d1", created_at: "2026-01-01T00:00:00Z", turn_count: 1 }]}
        onSelect={onSelect}
      />,
    );

    await user.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith("d1");
  });
});

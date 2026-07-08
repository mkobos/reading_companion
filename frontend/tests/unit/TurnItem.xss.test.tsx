import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TurnItem } from "../../src/discussion/TurnItem";

describe("TurnItem XSS safety", () => {
  it("renders an agent_response containing a script tag as inert visible text", () => {
    const malicious = "<script>alert(1)</script>";
    const { container } = render(
      <TurnItem
        turn={{
          turn_id: "t1",
          user_message: "hi",
          agent_response: malicious,
          viewport: { first_block_id: "000000", last_block_id: "000001" },
          created_at: "2026-01-01T00:00:00Z",
        }}
      />,
    );

    expect(screen.getByText(malicious)).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
  });
});

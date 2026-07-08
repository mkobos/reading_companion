import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ToolCallTrace } from "../../src/discussion/ToolCallTrace";

describe("ToolCallTrace", () => {
  it("renders nothing when toolCalls is undefined", () => {
    const { container } = render(<ToolCallTrace toolCalls={undefined} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when toolCalls is empty", () => {
    const { container } = render(<ToolCallTrace toolCalls={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a friendly label, input summary, and result summary per call", () => {
    render(
      <ToolCallTrace
        toolCalls={[
          { tool: "search_document", input_summary: "budget clause", result_summary: "3 matches" },
          { tool: "web_search", input_summary: "current interest rates" },
        ]}
      />,
    );

    expect(screen.getByText(/searched the document/i)).toBeInTheDocument();
    expect(screen.getByText(/budget clause/)).toBeInTheDocument();
    expect(screen.getByText(/3 matches/)).toBeInTheDocument();

    expect(screen.getByText(/searched the web/i)).toBeInTheDocument();
    expect(screen.getByText(/current interest rates/)).toBeInTheDocument();
  });
});

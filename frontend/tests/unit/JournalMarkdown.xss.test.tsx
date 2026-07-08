import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { JournalMarkdown } from "../../src/journal/JournalMarkdown";

describe("JournalMarkdown XSS safety", () => {
  it("renders a raw script tag as inert, never executed", () => {
    const malicious = "Before <script>window.__xss = true;</script> After";
    const { container } = render(<JournalMarkdown text={malicious} />);
    expect(container.querySelector("script")).toBeNull();
    expect((window as unknown as { __xss?: boolean }).__xss).toBeUndefined();
  });

  it("renders an onerror attribute as inert, never as a live attribute", () => {
    const malicious = '<img src=x onerror="window.__xss2 = true">';
    const { container } = render(<JournalMarkdown text={malicious} />);
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("[onerror]")).toBeNull();
    expect((window as unknown as { __xss2?: boolean }).__xss2).toBeUndefined();
  });

  it("renders a javascript: link as inert plain text, never a real anchor", () => {
    const { container } = render(<JournalMarkdown text="[click me](javascript:alert(1))" />);
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("click me")).toBeInTheDocument();
  });

  it("renders an ordinary https link as inert plain text too (product decision: no clickable links)", () => {
    const { container } = render(<JournalMarkdown text="[docs](https://example.com)" />);
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("docs")).toBeInTheDocument();
  });

  it("renders ordinary markdown (headings, emphasis) as formatted output", () => {
    render(<JournalMarkdown text={"## Heading\n\nSome **bold** text."} />);
    expect(screen.getByRole("heading", { name: "Heading" })).toBeInTheDocument();
    expect(screen.getByText("bold")).toBeInTheDocument();
  });
});

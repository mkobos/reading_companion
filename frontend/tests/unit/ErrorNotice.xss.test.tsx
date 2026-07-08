import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorNotice } from "../../src/ui/ErrorNotice";

describe("ErrorNotice XSS safety", () => {
  it("renders a script-tag-like error message as inert visible text", () => {
    const malicious = "<img src=x onerror=window.__xss=true>";
    const { container } = render(<ErrorNotice message={malicious} />);

    expect(screen.getByText(malicious)).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    expect((window as unknown as { __xss?: boolean }).__xss).toBeUndefined();
  });
});

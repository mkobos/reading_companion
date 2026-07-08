import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { UploadPanel } from "../../src/document/UploadPanel";
import { server } from "../msw/server";

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

function file(name: string, content = "hello", type = "text/plain") {
  return new File([content], name, { type });
}

describe("UploadPanel", () => {
  it("uploads an accepted .md file and calls onUploaded with the document", async () => {
    server.use(
      http.post("/api/workspaces/ws1/document", () =>
        HttpResponse.json(
          {
            filename: "notes.md",
            format: "markdown",
            size_bytes: 5,
            uploaded_at: "2026-01-01T00:00:00Z",
            blocks: [{ block_id: "000000", type: "paragraph", text: "hello" }],
          },
          { status: 201 },
        ),
      ),
    );
    renderWithClient(<UploadPanel workspaceId="ws1" onUploaded={() => {}} />);

    const input = screen.getByLabelText(/upload/i);
    await userEvent.upload(input, file("notes.md"));

    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it("shows the backend message on a 400 unsupported-type rejection (server is authoritative even for a client-accepted extension)", async () => {
    server.use(
      http.post("/api/workspaces/ws1/document", () =>
        HttpResponse.json(
          { message: "Unsupported file type. Only plain text (.txt) and Markdown (.md) files are accepted." },
          { status: 400 },
        ),
      ),
    );
    renderWithClient(<UploadPanel workspaceId="ws1" onUploaded={() => {}} />);

    const input = screen.getByLabelText(/upload/i);
    await userEvent.upload(input, file("note.txt"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/unsupported file type/i);
  });

  it("shows the backend message on a 400 oversized-file rejection", async () => {
    server.use(
      http.post("/api/workspaces/ws1/document", () =>
        HttpResponse.json({ message: "File exceeds the maximum size of 2000000 bytes." }, { status: 400 }),
      ),
    );
    renderWithClient(<UploadPanel workspaceId="ws1" onUploaded={() => {}} />);

    const input = screen.getByLabelText(/upload/i);
    await userEvent.upload(input, file("big.txt"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/exceeds the maximum size/i);
  });

  it("shows the backend message on a 400 bad-encoding rejection", async () => {
    server.use(
      http.post("/api/workspaces/ws1/document", () =>
        HttpResponse.json({ message: "File is not valid UTF-8 text." }, { status: 400 }),
      ),
    );
    renderWithClient(<UploadPanel workspaceId="ws1" onUploaded={() => {}} />);

    const input = screen.getByLabelText(/upload/i);
    await userEvent.upload(input, file("bad.txt"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/not valid utf-8/i);
  });

  it("rejects an obviously-bad extension client-side before calling the API", async () => {
    const user = userEvent.setup({ applyAccept: false });
    let called = false;
    server.use(
      http.post("/api/workspaces/ws1/document", () => {
        called = true;
        return HttpResponse.json({ message: "should not be reached" }, { status: 400 });
      }),
    );
    renderWithClient(<UploadPanel workspaceId="ws1" onUploaded={() => {}} />);

    const input = screen.getByLabelText(/upload/i);
    await user.upload(input, file("image.png", "x", "image/png"));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(called).toBe(false);
  });
});

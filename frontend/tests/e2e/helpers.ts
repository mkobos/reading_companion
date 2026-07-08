import type { APIRequestContext, Page } from "@playwright/test";

const COOKIE_NAME = "rc_last_workspace";
const API_BASE = "http://localhost:8000/api";

export async function createWorkspaceViaApi(request: APIRequestContext): Promise<string> {
  const response = await request.post(`${API_BASE}/workspaces`);
  const body = await response.json();
  return body.workspace_id as string;
}

export async function deleteWorkspaceViaApi(request: APIRequestContext, workspaceId: string) {
  await request.delete(`${API_BASE}/workspaces/${workspaceId}`);
}

export async function uploadDocumentViaApi(
  request: APIRequestContext,
  workspaceId: string,
  filename: string,
  content: string,
) {
  await request.post(`${API_BASE}/workspaces/${workspaceId}/document`, {
    multipart: { file: { name: filename, mimeType: "text/markdown", buffer: Buffer.from(content) } },
  });
}

export async function startDiscussionViaApi(
  request: APIRequestContext,
  workspaceId: string,
  message: string,
): Promise<string> {
  const response = await request.post(`${API_BASE}/workspaces/${workspaceId}/discussions`, {
    data: {
      message,
      viewport: { first_block_id: "000000", last_block_id: "000000" },
    },
  });
  const body = await response.json();
  return body.discussion_id as string;
}

export async function setLastWorkspaceCookie(page: Page, workspaceId: string) {
  await page.context().addCookies([
    {
      name: COOKIE_NAME,
      value: workspaceId,
      url: "http://localhost:5173",
    },
  ]);
}

export async function readLastWorkspaceCookie(page: Page): Promise<string | undefined> {
  const cookies = await page.context().cookies("http://localhost:5173");
  return cookies.find((c) => c.name === COOKIE_NAME)?.value;
}

export async function clearCookies(page: Page) {
  await page.context().clearCookies();
}

import { expect, test } from "@playwright/test";
import {
  createWorkspaceViaApi,
  setLastWorkspaceCookie,
  startDiscussionViaApi,
  uploadDocumentViaApi,
} from "../helpers";

// discussions.feature: continuing an existing discussion appends a new
// turn to the thread view.
test("submitting a follow-up message appends a new turn to the thread", async ({ page, request }) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", "# Title\n\nSome content to discuss.");
  await startDiscussionViaApi(request, workspaceId, "What is this about?");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await page.getByText(/1 turn/i).click();

  await expect(page.getByText("This is a fake discussion-agent response.")).toBeVisible();

  const composer = page.getByRole("textbox");
  await composer.fill("Tell me more");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText("Tell me more")).toBeVisible();
  await expect(page.getByText("This is a fake discussion-agent response.")).toHaveCount(2);
});

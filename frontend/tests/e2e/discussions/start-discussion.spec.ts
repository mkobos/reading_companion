import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// discussions.feature: starting a general (no-anchor) discussion from the
// reading view surfaces the agent's response synchronously (requires the
// backend running with DISCUSSION_AGENT_FAKE=1 for a canned response).
test("starting a discussion renders the agent's response", async ({ page, request }) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", "# Title\n\nSome content to discuss.");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await expect(page.getByText("Some content to discuss.")).toBeVisible();

  const composer = page.getByPlaceholder(/ask about this document/i);
  await composer.fill("What is this document about?");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText("This is a fake discussion-agent response.")).toBeVisible();
});

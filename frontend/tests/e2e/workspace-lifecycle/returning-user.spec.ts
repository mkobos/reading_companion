import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// workspace-lifecycle.feature: "Returning user goes straight to their last
// workspace, no new one created" — verified by proving the SAME workspace
// (with its already-uploaded document) is shown, not a fresh empty one.
test("a returning user with a valid cookie is sent straight to that workspace", async ({
  page,
  request,
}) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "existing.md", "# Existing document");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto("/");
  await page.waitForURL(new RegExp(`/w/${workspaceId}$`));

  await expect(page.getByText("Existing document")).toBeVisible();
});

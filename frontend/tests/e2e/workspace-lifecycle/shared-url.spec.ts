import { expect, test } from "@playwright/test";
import { clearCookies, createWorkspaceViaApi, readLastWorkspaceCookie } from "../helpers";

// workspace-lifecycle.feature: direct shared URL grants full access + cookie updated.
test("visiting a workspace URL directly (no cookie) grants full access and updates the cookie", async ({
  page,
  request,
}) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await clearCookies(page);

  await page.goto(`/w/${workspaceId}`);

  await expect(page.getByLabel(/upload/i)).toBeVisible();

  const cookie = await readLastWorkspaceCookie(page);
  expect(cookie).toBe(workspaceId);
});

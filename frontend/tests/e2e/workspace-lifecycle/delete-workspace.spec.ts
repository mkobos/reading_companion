import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, setLastWorkspaceCookie } from "../helpers";

// workspace-lifecycle.feature: delete workspace -> 404 after, redirect to fresh.
test("deleting a workspace redirects to a fresh one and the old URL 404s afterward", async ({
  page,
  request,
}) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await page.getByRole("button", { name: /delete workspace/i }).click();
  await page.getByRole("dialog").getByRole("button", { name: /delete/i }).click();

  await page.waitForURL((url) => !url.pathname.endsWith(`/w/${workspaceId}`));
  const newId = page.url().split("/w/")[1];
  expect(newId).not.toBe(workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await expect(page.getByRole("heading", { name: /workspace not found/i })).toBeVisible();
});

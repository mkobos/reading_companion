import { expect, test } from "@playwright/test";
import { clearCookies, readLastWorkspaceCookie } from "../helpers";

// workspace-lifecycle.feature: "New user gets empty workspace + cookie + redirect"
test("a new user with no cookie lands on a fresh workspace and gets a cookie", async ({ page }) => {
  await clearCookies(page);
  await page.goto("/");

  await page.waitForURL(/\/w\/.+/);
  const workspaceId = page.url().split("/w/")[1];
  expect(workspaceId).toBeTruthy();

  const cookie = await readLastWorkspaceCookie(page);
  expect(cookie).toBe(workspaceId);

  await expect(page.getByLabel(/upload/i)).toBeVisible();
});

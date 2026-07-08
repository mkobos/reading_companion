import { expect, test } from "@playwright/test";
import { readLastWorkspaceCookie } from "../helpers";

// workspace-lifecycle.feature: explicit "new workspace" action; original
// workspace (W1) remains intact and directly reachable afterward.
test("explicit new-workspace action creates W2 while W1 stays reachable", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/");
  await page.waitForURL(/\/w\/.+/);
  const w1 = page.url().split("/w/")[1]!;

  await page.getByRole("button", { name: /new workspace/i }).click();
  await page.waitForURL((url) => !url.pathname.endsWith(`/w/${w1}`));
  const w2 = page.url().split("/w/")[1]!;
  expect(w2).not.toBe(w1);

  const cookie = await readLastWorkspaceCookie(page);
  expect(cookie).toBe(w2);

  // W1 is still intact and directly reachable.
  await page.goto(`/w/${w1}`);
  await expect(page.getByLabel(/upload/i)).toBeVisible();
});

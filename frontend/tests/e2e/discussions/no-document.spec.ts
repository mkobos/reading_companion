import { expect, test } from "@playwright/test";

// discussions.feature: a workspace with no document shows only the upload
// panel — no discussion composer/panel anywhere on the page.
test("a workspace with no document shows only the upload panel, no discussion UI", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/");
  await page.waitForURL(/\/w\/.+/);

  await expect(page.getByLabel(/upload/i)).toBeVisible();
  await expect(page.getByPlaceholder(/ask about this document/i)).toHaveCount(0);
  // The upload input is type="file", not role=textbox — no discussion
  // composer (a textarea) should be present anywhere on the page.
  await expect(page.getByRole("textbox")).toHaveCount(0);
});

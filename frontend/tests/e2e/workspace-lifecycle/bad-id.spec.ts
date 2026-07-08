import { expect, test } from "@playwright/test";

// workspace-lifecycle.feature: nonexistent/malformed ID -> not-found page,
// create action, nothing created until invoked.
test("a malformed or nonexistent workspace ID shows not-found and creates nothing until invoked", async ({
  page,
}) => {
  await page.goto("/w/this-does-not-exist-at-all");

  await expect(page.getByRole("heading", { name: /workspace not found/i })).toBeVisible();
  const createButton = page.getByRole("button", { name: /create a new workspace/i });
  await expect(createButton).toBeVisible();

  // Nothing created yet: reloading the same bad URL still shows not-found.
  await page.reload();
  await expect(page.getByRole("heading", { name: /workspace not found/i })).toBeVisible();

  await createButton.click();
  await page.waitForURL(/\/w\/.+/);
  await expect(page.getByLabel(/upload/i)).toBeVisible();
});

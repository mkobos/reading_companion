import { expect, test } from "@playwright/test";

// document-upload.feature "Accepted upload" + reading-view.feature
// "Rendering the document" — plus this phase's required live XSS check:
// a <script>-tag-like string embedded in the document renders as inert text.
test("uploading a .md file renders it as blocks in order", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/");
  await page.waitForURL(/\/w\/.+/);

  const content = ["# My Document", "", "A normal paragraph.", "", "A second paragraph."].join(
    "\n",
  );

  await page.getByLabel(/upload/i).setInputFiles({
    name: "doc.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(content),
  });

  await expect(page.getByRole("heading", { name: "My Document" })).toBeVisible();
  await expect(page.getByText("A normal paragraph.")).toBeVisible();
  await expect(page.getByText("A second paragraph.")).toBeVisible();

  // Immutability: no upload affordance remains once a document exists.
  await expect(page.getByLabel(/upload/i)).toHaveCount(0);
});

test("a <script>-tag-like string in a plain-text document renders as inert visible text", async ({
  page,
}) => {
  await page.context().clearCookies();
  await page.goto("/");
  await page.waitForURL(/\/w\/.+/);

  const malicious = "<script>window.__xss_ran = true;</script> this looks dangerous but is not.";
  await page.getByLabel(/upload/i).setInputFiles({
    name: "doc.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(`Title\n\n${malicious}\n`),
  });

  await expect(page.getByText(malicious)).toBeVisible();
  await expect(page.locator("script:not([type='module']):not([src])")).toHaveCount(0);
  const xssRan = await page.evaluate(() => (window as unknown as { __xss_ran?: boolean }).__xss_ran);
  expect(xssRan).toBeUndefined();
});

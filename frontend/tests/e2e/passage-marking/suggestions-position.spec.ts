import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, selectTextInBlock, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// passage-marking: the suggestions popover must appear immediately in the
// viewport, vertically aligned with the marked passage, even when the mark
// is made far down a long document — the user should never have to scroll
// to see it.
test("marking a passage near the bottom of a long document shows the popover without scrolling", async ({
  page,
  request,
}) => {
  const workspaceId = await createWorkspaceViaApi(request);
  const paragraphs = Array.from({ length: 50 }, (_, i) => `Paragraph number ${i + 1} of the document.`);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", `# Title\n\n${paragraphs.join("\n\n")}`);
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  const lastBlockId = "000050"; // 000000 = heading, 000001..000050 = paragraphs

  // A real user can only select text that's already on screen, so scroll the
  // target block into view first (as they would) before marking it.
  await page.locator(`[data-block-id="${lastBlockId}"]`).scrollIntoViewIfNeeded();
  await expect(page.getByText("Paragraph number 50 of the document.")).toBeVisible();

  const scrollBefore = await page.evaluate(() => window.scrollY);
  await selectTextInBlock(page, lastBlockId, 0, "Paragraph".length);

  const popover = page.getByRole("dialog", { name: "Passage suggestions" });
  await expect(popover).toBeVisible();

  const scrollAfter = await page.evaluate(() => window.scrollY);
  expect(scrollAfter).toBe(scrollBefore); // marking must not itself cause a scroll

  const box = await popover.boundingBox();
  expect(box).not.toBeNull();
  const viewportSize = page.viewportSize();
  expect(viewportSize).not.toBeNull();
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.y).toBeLessThan(viewportSize!.height);
});

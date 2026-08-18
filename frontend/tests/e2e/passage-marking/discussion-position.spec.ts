import { expect, test } from "@playwright/test";
import {
  createWorkspaceViaApi,
  setLastWorkspaceCookie,
  startDiscussionViaApi,
  uploadDocumentViaApi,
  type Passage,
} from "../helpers";

// passage-marking: persisted discussions must render as margin boxes
// aligned to their anchor passage's height (not stacked at the top),
// never overlapping each other, and previewing their anchor text — and
// clicking a box must highlight that exact passage in the reading column.

function paragraphAnchor(n: number, blockId: string): Passage {
  const text = `Paragraph number ${n} of the document.`;
  return { first_block_id: blockId, first_block_offset: 0, last_block_id: blockId, last_block_offset: text.length, text };
}

async function setUpLongDocument(request: Parameters<typeof createWorkspaceViaApi>[0]) {
  const workspaceId = await createWorkspaceViaApi(request);
  const paragraphs = Array.from({ length: 50 }, (_, i) => `Paragraph number ${i + 1} of the document.`);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", `# Title\n\n${paragraphs.join("\n\n")}`);
  return workspaceId;
}

test("discussion boxes align with their anchor's height and preview its text, ordered by document position", async ({
  page,
  request,
}) => {
  const workspaceId = await setUpLongDocument(request);
  const earlyId = await startDiscussionViaApi(request, workspaceId, "About para 10", paragraphAnchor(10, "000010"));
  const lateId = await startDiscussionViaApi(request, workspaceId, "About para 40", paragraphAnchor(40, "000040"));
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(page.getByText("Paragraph number 1 of the document.")).toBeVisible();

  const earlyBox = page.getByTestId(`discussion-box-${earlyId}`);
  const lateBox = page.getByTestId(`discussion-box-${lateId}`);
  await expect(earlyBox).toBeVisible();
  await expect(lateBox).toBeVisible();
  await expect(earlyBox.getByTestId("discussion-anchor-text")).toHaveText(
    "“Paragraph number 10 of the document.”",
  );

  const earlyBlockBox = await page.locator('[data-block-id="000010"]').boundingBox();
  const lateBlockBox = await page.locator('[data-block-id="000040"]').boundingBox();
  const earlyBoxBox = await earlyBox.boundingBox();
  const lateBoxBox = await lateBox.boundingBox();
  expect(earlyBlockBox).not.toBeNull();
  expect(lateBlockBox).not.toBeNull();
  expect(earlyBoxBox).not.toBeNull();
  expect(lateBoxBox).not.toBeNull();

  // Aligned to their own anchor's height within a small tolerance...
  expect(Math.abs(earlyBoxBox!.y - earlyBlockBox!.y)).toBeLessThan(80);
  // ...and ordered: the later paragraph's box sits below the earlier one's.
  expect(lateBoxBox!.y).toBeGreaterThan(earlyBoxBox!.y);
});

test("discussion boxes anchored close together do not overlap", async ({ page, request }) => {
  const workspaceId = await setUpLongDocument(request);
  const firstId = await startDiscussionViaApi(request, workspaceId, "About para 10", paragraphAnchor(10, "000010"));
  const secondId = await startDiscussionViaApi(request, workspaceId, "About para 11", paragraphAnchor(11, "000011"));
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(page.getByText("Paragraph number 1 of the document.")).toBeVisible();

  const firstBox = await page.getByTestId(`discussion-box-${firstId}`).boundingBox();
  const secondBox = await page.getByTestId(`discussion-box-${secondId}`).boundingBox();
  expect(firstBox).not.toBeNull();
  expect(secondBox).not.toBeNull();

  const [top, bottom] =
    firstBox!.y <= secondBox!.y ? [firstBox!, secondBox!] : [secondBox!, firstBox!];
  expect(bottom.y).toBeGreaterThanOrEqual(top.y + top.height - 1); // -1px float-rounding slack
});

test("clicking a discussion box highlights its passage, which clears when going back to the list", async ({
  page,
  request,
}) => {
  const workspaceId = await setUpLongDocument(request);
  const discussionId = await startDiscussionViaApi(
    request,
    workspaceId,
    "About para 10",
    paragraphAnchor(10, "000010"),
  );
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(page.getByText("Paragraph number 1 of the document.")).toBeVisible();

  const mark = page.locator('[data-block-id="000010"] mark');
  await expect(mark).toHaveCount(0);

  await page.getByTestId(`discussion-box-${discussionId}`).click();
  await expect(mark).toHaveText("Paragraph number 10 of the document.");

  await page.getByRole("button", { name: "Back to discussions" }).click();
  await expect(mark).toHaveCount(0);
});

test("clicking an anchored discussion box unfolds the thread in place, near the anchor position", async ({
  page,
  request,
}) => {
  const workspaceId = await setUpLongDocument(request);
  const targetId = await startDiscussionViaApi(
    request,
    workspaceId,
    "About para 40",
    paragraphAnchor(40, "000040"),
  );
  const belowId = await startDiscussionViaApi(
    request,
    workspaceId,
    "About para 41",
    paragraphAnchor(41, "000041"),
  );
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(page.getByText("Paragraph number 1 of the document.")).toBeVisible();
  await page.locator('[data-block-id="000040"]').scrollIntoViewIfNeeded();

  const targetBox = page.getByTestId(`discussion-box-${targetId}`);
  const belowBox = page.getByTestId(`discussion-box-${belowId}`);
  await targetBox.click();

  // The thread unfolds where the box was, not at the top of the page.
  const targetBlockBox = await page.locator('[data-block-id="000040"]').boundingBox();
  const expandedBox = await targetBox.boundingBox();
  expect(targetBlockBox).not.toBeNull();
  expect(expandedBox).not.toBeNull();
  expect(Math.abs(expandedBox!.y - targetBlockBox!.y)).toBeLessThan(80);
  expect(expandedBox!.y).toBeGreaterThan(200); // nowhere near page top

  // The other anchored discussion's box is still there, pushed below.
  await expect(belowBox).toBeVisible();
  const belowBoxBox = await belowBox.boundingBox();
  expect(belowBoxBox).not.toBeNull();
  expect(belowBoxBox!.y).toBeGreaterThanOrEqual(expandedBox!.y + expandedBox!.height - 1);
});

test("on a narrow viewport, discussions render as a plain stacked list, not anchor-positioned", async ({
  page,
  request,
}) => {
  const workspaceId = await setUpLongDocument(request);
  const discussionId = await startDiscussionViaApi(
    request,
    workspaceId,
    "About para 40",
    paragraphAnchor(40, "000040"),
  );
  await setLastWorkspaceCookie(page, workspaceId);

  await page.setViewportSize({ width: 500, height: 900 });
  await page.goto(`/w/${workspaceId}`);
  await expect(page.getByText("Paragraph number 1 of the document.")).toBeVisible();

  const box = page.getByTestId(`discussion-box-${discussionId}`);
  await expect(box).toBeVisible();
  const position = await box.evaluate((el) => getComputedStyle(el).position);
  expect(position).toBe("static");
});

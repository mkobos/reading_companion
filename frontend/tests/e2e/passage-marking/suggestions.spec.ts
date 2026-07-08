import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, selectTextInBlock, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// passage-marking + suggestions: marking a passage shows a popover with 4
// suggested questions (FakeLlmClient always returns exactly 4); clicking
// one starts a discussion anchored to that passage.
test("marking a passage shows 4 suggestions, and clicking one starts a discussion", async ({
  page,
  request,
}) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", "# Title\n\nSome content to discuss.");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await expect(page.getByText("Some content to discuss.")).toBeVisible();

  await selectTextInBlock(page, "000001", 0, 4); // "Some"

  const popover = page.getByRole("dialog", { name: "Passage suggestions" });
  await expect(popover).toBeVisible();
  const suggestionButtons = popover.getByRole("button").filter({ hasNotText: "×" });
  await expect(suggestionButtons).toHaveCount(4);

  await suggestionButtons.first().click();

  await expect(popover).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "Discussions", selected: true })).toBeVisible();
});

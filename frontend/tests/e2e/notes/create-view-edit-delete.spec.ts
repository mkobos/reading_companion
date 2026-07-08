import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, selectTextInBlock, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// notes CRUD: marking a passage anchors a note composer in the Notes tab;
// created notes show an inline reading-column indicator; edit and delete
// both work, and delete goes through the ConfirmDialog.
test("create, view, edit, and delete a note anchored to a marked passage", async ({ page, request }) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", "# Title\n\nSome content to discuss.");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);
  await expect(page.getByText("Some content to discuss.")).toBeVisible();

  await selectTextInBlock(page, "000001", 0, 4); // "Some"

  await page.getByRole("tab", { name: "Notes" }).click();
  await expect(page.getByText(/new note on/i)).toContainText("Some");

  const composer = page.getByRole("textbox");
  await composer.fill("This is my note.");
  await page.getByRole("button", { name: /add note/i }).click();

  await expect(page.getByText("This is my note.")).toBeVisible();
  // An inline indicator appears in the reading column next to the anchored block.
  await expect(page.getByRole("button", { name: /^note:/i })).toBeVisible();

  // Edit.
  await page.getByRole("button", { name: "Edit" }).click();
  const editBox = page.getByRole("textbox");
  await editBox.fill("Updated note text.");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Updated note text.")).toBeVisible();
  await expect(page.getByText("This is my note.")).toHaveCount(0);

  // Delete via the ConfirmDialog. Playwright's role `name` is a
  // case-insensitive substring match by default, and the page also has an
  // unrelated "Delete workspace" button — `exact: true` disambiguates.
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Delete note" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Delete" }).click();

  await expect(page.getByText("Updated note text.")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^note:/i })).toHaveCount(0);
});

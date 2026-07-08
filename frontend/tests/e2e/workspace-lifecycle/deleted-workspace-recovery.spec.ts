import { expect, test } from "@playwright/test";
import {
  createWorkspaceViaApi,
  deleteWorkspaceViaApi,
  readLastWorkspaceCookie,
  setLastWorkspaceCookie,
} from "../helpers";

// workspace-lifecycle.feature: cookie pointing at a deleted workspace ->
// toast + fresh workspace + cookie updated.
test("a cookie pointing at a deleted workspace recovers with a toast and a fresh workspace", async ({
  page,
  request,
}) => {
  const deletedId = await createWorkspaceViaApi(request);
  await deleteWorkspaceViaApi(request, deletedId);
  await setLastWorkspaceCookie(page, deletedId);

  await page.goto("/");

  await expect(page.getByRole("alert")).toContainText(/no longer available|deleted/i);
  await page.waitForURL(/\/w\/.+/);

  const newId = page.url().split("/w/")[1];
  expect(newId).toBeTruthy();
  expect(newId).not.toBe(deletedId);

  const cookie = await readLastWorkspaceCookie(page);
  expect(cookie).toBe(newId);
});

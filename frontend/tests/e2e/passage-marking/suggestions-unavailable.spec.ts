import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, selectTextInBlock, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// passage-marking + suggestions (503 path): the e2e backend process is
// started once for the whole suite with LLM_FAKE=1 (not
// LLM_FAKE_FORCE_ERROR=1), so a real 503 can't be triggered for just this
// spec without restarting the backend. Instead, intercept the suggestions
// call at the network layer and fulfill it with a synthetic 503 — this
// still exercises the frontend's real error-handling code path against a
// realistic backend response shape.
test("a 503 from the suggestions endpoint shows a free-form fallback input", async ({ page, request }) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", "# Title\n\nSome content to discuss.");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.route(`**/api/workspaces/${workspaceId}/suggestions`, (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );

  await page.goto(`/w/${workspaceId}`);
  await expect(page.getByText("Some content to discuss.")).toBeVisible();

  await selectTextInBlock(page, "000001", 0, 4); // "Some"

  const popover = page.getByRole("dialog", { name: "Passage suggestions" });
  await expect(popover).toBeVisible();
  await expect(popover.getByRole("alert")).toBeVisible();
  await expect(popover.getByRole("textbox")).toBeVisible();

  await popover.getByRole("textbox").fill("What does this mean?");
  await popover.getByRole("button", { name: "Ask" }).click();

  await expect(popover).toHaveCount(0);
  await expect(page.getByText("What does this mean?")).toBeVisible();
});

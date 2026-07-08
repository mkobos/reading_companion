import { expect, test } from "@playwright/test";
import { createWorkspaceViaApi, setLastWorkspaceCookie, uploadDocumentViaApi } from "../helpers";

// discussions.feature / security.feature: a simulated agent failure (fake
// client sentinel token) surfaces the error + Resend UI, and nothing is
// persisted — reloading shows no discussion at all.
test("a simulated agent failure shows an error with Resend and persists nothing", async ({
  page,
  request,
}) => {
  const workspaceId = await createWorkspaceViaApi(request);
  await uploadDocumentViaApi(request, workspaceId, "doc.md", "# Title\n\nSome content to discuss.");
  await setLastWorkspaceCookie(page, workspaceId);

  await page.goto(`/w/${workspaceId}`);

  const composer = page.getByPlaceholder(/ask about this document/i);
  await composer.fill("__SIMULATE_AGENT_FAILURE__");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByRole("button", { name: /resend/i })).toBeVisible();

  await page.reload();
  await expect(page.getByText(/no discussions/i)).toBeVisible();
});

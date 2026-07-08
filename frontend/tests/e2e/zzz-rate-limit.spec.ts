import { expect, test } from "@playwright/test";

// security.feature / plan §6.6: uniform 429 handling for create/upload, no
// retry-storm. Deliberately exhausts the real backend's per-IP rate limit
// for workspace creation, then drives the actual UI action once and
// confirms it surfaces the message without firing a burst of retries.
test("exhausting the create-workspace rate limit surfaces the message with no retry-storm", async ({
  page,
}) => {
  await page.context().clearCookies();
  await page.goto("/");
  await page.waitForURL(/\/w\/.+/);

  // Drive the shared per-IP limiter to its ceiling via direct API calls
  // through the same dev proxy the app uses, so the very next UI action is
  // guaranteed to be rate-limited regardless of what earlier tests consumed.
  let sawRateLimit = false;
  for (let i = 0; i < 50 && !sawRateLimit; i += 1) {
    const response = await page.request.post("/api/workspaces");
    if (response.status() === 429) sawRateLimit = true;
  }
  expect(sawRateLimit).toBe(true);

  let createRequestCount = 0;
  page.on("request", (req) => {
    if (req.method() === "POST" && req.url().endsWith("/api/workspaces")) {
      createRequestCount += 1;
    }
  });

  await page.getByRole("button", { name: /new workspace/i }).click();

  await expect(page.getByRole("alert")).toBeVisible();

  // Give any (incorrect) auto-retry behavior a window to fire, then assert
  // the client issued exactly one request for this one user action.
  await page.waitForTimeout(1000);
  expect(createRequestCount).toBe(1);
});

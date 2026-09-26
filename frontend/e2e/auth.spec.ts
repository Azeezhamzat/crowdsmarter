import { expect, test } from "@playwright/test";

test("sign-in screen communicates human-led product positioning", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Continue the reasoning, not just the record." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("an organisation owner can invite a person who creates their own account", async ({ browser }) => {
  test.skip(!process.env.E2E_EMAIL || !process.env.E2E_PASSWORD);

  const ownerContext = await browser.newContext();
  const ownerPage = await ownerContext.newPage();
  await ownerPage.goto("/login");
  await ownerPage.getByLabel("Email address").fill(process.env.E2E_EMAIL ?? "");
  await ownerPage.getByLabel("Password").fill(process.env.E2E_PASSWORD ?? "");
  await ownerPage.getByRole("button", { name: "Sign in" }).click();

  const suffix = Date.now().toString();
  const organisationName = `Invitation Organisation ${suffix}`;
  const invitedEmail = `invitee-${suffix}@example.com`;
  await ownerPage.getByLabel("Name").fill(organisationName);
  await ownerPage.getByLabel("URL identifier").fill(`invitation-${suffix}`);
  await ownerPage.getByRole("button", { name: "Create organisation" }).click();
  await ownerPage.getByRole("link", { name: new RegExp(organisationName) }).click();

  await ownerPage.getByLabel("Email address").fill(invitedEmail);
  await ownerPage.getByLabel("Role", { exact: true }).selectOption("contributor");
  await ownerPage.getByRole("button", { name: "Send invitation" }).click();
  const acceptanceUrl = await ownerPage.locator(".copyable-link").textContent();
  expect(acceptanceUrl).toContain("#token=");

  const invitedContext = await browser.newContext();
  const invitedPage = await invitedContext.newPage();
  await invitedPage.goto(acceptanceUrl ?? "");
  await invitedPage.getByLabel("First name").fill("Invited");
  await invitedPage.getByLabel("Last name").fill("Person");
  await invitedPage.getByLabel("Create password").fill("A-strong-invited-password-123");
  await invitedPage.getByLabel("Confirm password").fill("A-strong-invited-password-123");
  await invitedPage.getByRole("button", { name: "Create account and accept" }).click();

  await expect(invitedPage.getByRole("heading", { name: organisationName })).toBeVisible();
  await ownerContext.close();
  await invitedContext.close();
});

test("public landing page presents facilitation before the supporting platform", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Make difficult decisions together, with a process people can trust/i })).toBeVisible();
  await expect(page.getByRole("link", { name: "Discuss a decision" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Set up a commons" }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: /distinction is facilitated continuity, not more software/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /designed to support scrutiny/i })).toBeVisible();
});


test("public decision enquiry form is available", async ({ page }) => {
  await page.goto("/request-demo");
  await expect(page.getByRole("heading", { name: /Explore how CrowdSmarter could facilitate a real decision/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Send decision enquiry/i })).toBeVisible();
});

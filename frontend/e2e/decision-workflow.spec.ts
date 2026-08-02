import { expect, test } from "@playwright/test";

// Requires E2E_EMAIL and E2E_PASSWORD for an existing account. The test creates
// its own tenant and exercises the first complete decision workflow slice.
test("create and frame a governed decision", async ({ page }) => {
  test.skip(!process.env.E2E_EMAIL || !process.env.E2E_PASSWORD);

  await page.goto("/login");
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL ?? "");
  await page.getByLabel("Password").fill(process.env.E2E_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();

  const suffix = Date.now().toString();
  await page.getByLabel("Name").fill(`E2E Organisation ${suffix}`);
  await page.getByLabel("URL identifier").fill(`e2e-${suffix}`);
  await page.getByRole("button", { name: "Create organisation" }).click();
  await page.getByRole("link", { name: new RegExp(`E2E Organisation ${suffix}`) }).click();
  await page.getByRole("link", { name: "Decision workspaces" }).click();
  await page.getByRole("link", { name: /Decisions/ }).click();

  await page.getByLabel("Working title").fill("Choose an initial customer segment");
  await page.getByLabel("Decision question").fill("Which customer segment should we serve first?");
  await page.getByRole("button", { name: "Create draft" }).click();

  await expect(page.getByRole("heading", { name: "Choose an initial customer segment" })).toBeVisible();
  await page.getByLabel("Purpose").fill("Focus limited commercial capacity.");
  await page.getByLabel("Scope").fill("Initial UK and Ireland launch.");
  await page.getByRole("button", { name: "Save framing" }).click();
  await expect(page.getByText("Decision framing saved.")).toBeVisible();
});

// Phase 3 smoke coverage: structured records are created through the browser,
// while lifecycle authority remains with a human decision owner.
test("record options, evidence, assumptions, and risks", async ({ page }) => {
  test.skip(!process.env.E2E_EMAIL || !process.env.E2E_PASSWORD);

  await page.goto("/login");
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL ?? "");
  await page.getByLabel("Password").fill(process.env.E2E_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();

  const suffix = Date.now().toString();
  await page.getByLabel("Name").fill(`Reasoning Organisation ${suffix}`);
  await page.getByLabel("URL identifier").fill(`reasoning-${suffix}`);
  await page.getByRole("button", { name: "Create organisation" }).click();
  await page.getByRole("link", { name: new RegExp(`Reasoning Organisation ${suffix}`) }).click();
  await page.getByRole("link", { name: "Decision workspaces" }).click();
  await page.getByRole("link", { name: /Decisions/ }).click();

  await page.getByLabel("Working title").fill("Pilot a crop monitoring system");
  await page.getByLabel("Decision question").fill("Should we run a three-month pilot?");
  await page.getByRole("button", { name: "Create draft" }).click();
  await page.getByRole("link", { name: "Open structured review" }).click();

  await page.getByLabel("Title").fill("Run a limited pilot");
  await page.getByLabel("Description").fill("Test the system on three farms for three months.");
  await page.getByRole("button", { name: "Add option" }).click();
  await expect(page.getByRole("heading", { name: "Run a limited pilot" })).toBeVisible();

  await page.getByRole("link", { name: "evidence" }).click();
  await page.getByLabel("Title").fill("Comparable pilot report");
  await page.getByLabel("Summary").fill("A comparable pilot found earlier pest detection.");
  await page.getByLabel("Source reference").fill("Comparable pilot report 2026");
  await page.getByRole("button", { name: "Add evidence" }).click();
  await expect(page.getByRole("heading", { name: "Comparable pilot report" })).toBeVisible();

  await page.getByRole("link", { name: "assumptions" }).click();
  await page.getByLabel("Assumption").fill("Field staff can support the weekly workload.");
  await page.getByLabel("What changes if it is false?").fill("The pilot scope must be reduced.");
  await page.getByRole("button", { name: "Add assumption" }).click();
  await expect(page.getByRole("heading", { name: "Field staff can support the weekly workload." })).toBeVisible();

  await page.getByRole("link", { name: "risks" }).click();
  await page.getByLabel("Title").fill("Low staff adoption");
  await page.getByLabel("Description").fill("The workflow may not fit daily field operations.");
  await page.getByLabel("Response plan").fill("Involve field staff in configuration and training.");
  await page.getByRole("button", { name: "Add risk" }).click();
  await expect(page.getByRole("heading", { name: "Low staff adoption" })).toBeVisible();
});

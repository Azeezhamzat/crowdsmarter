import { expect, test } from "@playwright/test";

const publicRoutes = ["/", "/login", "/request-demo", "/this-route-does-not-exist"];

for (const route of publicRoutes) {
  test(`${route} exposes one main landmark and a working skip link`, async ({ page }) => {
    await page.goto(route);

    await expect(page.locator("main")).toHaveCount(1);
    const skipLink = page.getByRole("link", { name: "Skip to main content" });
    await skipLink.focus();
    await expect(skipLink).toBeFocused();
    await skipLink.press("Enter");
    await expect(page.locator("#main-content")).toBeFocused();
  });
}

test("public workflow follows the ARIA tabs keyboard pattern", async ({ page }) => {
  await page.goto("/");

  const tablist = page.getByRole("tablist", { name: /workflow stages/i });
  await expect(tablist).toHaveAttribute("aria-orientation", "horizontal");

  const sense = page.getByRole("tab", { name: /sense/i });
  await sense.focus();
  await sense.press("ArrowRight");

  const interpret = page.getByRole("tab", { name: /interpret/i });
  await expect(interpret).toBeFocused();
  await expect(interpret).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tabpanel", { name: /interpret/i })).toHaveAttribute("tabindex", "0");
});

test("unknown routes provide a named recovery page", async ({ page }) => {
  await page.goto("/missing-destination");

  await expect(page).toHaveTitle(/Page not found — The CrowdSmarter/);
  await expect(page.getByRole("heading", { name: /destination is not part of this workspace/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /return to the public site/i })).toHaveAttribute("href", "/");
});

test("key public forms expose programmatic labels", async ({ page }) => {
  await page.goto("/request-demo");

  await expect(page.getByLabel("Full name *")).toBeVisible();
  await expect(page.getByLabel("Work email *")).toBeVisible();
  await expect(page.getByLabel("Organisation name *")).toBeVisible();
  await expect(page.getByLabel(/consent to being contacted/i)).toBeVisible();

  await page.goto("/login");
  await expect(page.getByLabel("Email address")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
});

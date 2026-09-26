import { expect, test } from "@playwright/test";

const publicRoutes = [
  "/",
  "/login",
  "/signup",
  "/request-demo",
  "/verify-email-change",
  "/this-route-does-not-exist",
];

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

test("public process exposes a logical heading hierarchy", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 2, name: /a facilitated decision, supported by a connected system/i })).toBeVisible();
  for (const stage of ["Anticipate", "Deliberate", "Decide", "Act", "Learn"]) {
    await expect(page.getByRole("heading", { level: 3, name: stage, exact: true })).toBeVisible();
  }
});

test("unknown routes provide a named recovery page", async ({ page }) => {
  await page.goto("/missing-destination");

  await expect(page).toHaveTitle(/Page not found - CrowdSmarter/);
  await expect(page.getByRole("heading", { name: /destination is not part of this workspace/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /return to the public site/i })).toHaveAttribute("href", "/");
});

test("key public forms expose programmatic labels", async ({ page }) => {
  await page.goto("/request-demo");

  await expect(page.getByLabel("Full name *")).toBeVisible();
  await expect(page.getByLabel("Work email *")).toBeVisible();
  await expect(page.getByLabel("Organisation *")).toBeVisible();
  await expect(page.getByLabel(/consent to being contacted/i)).toBeVisible();

  await page.goto("/login");
  await expect(page.getByLabel("Email address")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
});

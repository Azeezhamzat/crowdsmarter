import { expect, test } from "@playwright/test";

const viewports = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "tablet", width: 834, height: 1112 },
  { name: "mobile", width: 390, height: 844 },
];

for (const viewport of viewports) {
  test(`homepage remains readable without horizontal overflow at ${viewport.name} width`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /Make difficult decisions together, with a process people can trust/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /A facilitated decision, supported by a connected system/i })).toBeVisible();

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);

    const mainBounds = await page.locator("main").boundingBox();
    expect(mainBounds).not.toBeNull();
    expect(mainBounds?.x ?? -1).toBeGreaterThanOrEqual(0);
    expect((mainBounds?.x ?? 0) + (mainBounds?.width ?? 0)).toBeLessThanOrEqual(viewport.width + 1);
  });
}

test("each lifecycle stage has distinct explanatory content", async ({ page }) => {
  await page.goto("/");

  for (const stage of ["Anticipate", "Deliberate", "Decide", "Act", "Learn"]) {
    const heading = page.getByRole("heading", { name: stage, exact: true });
    await expect(heading).toBeVisible();
    await expect(heading.locator("xpath=following-sibling::p")).not.toHaveText("");
  }
});


test("sticky navigation does not cover anchored section headings", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "How it works" }).click();

  const headerBounds = await page.locator(".public-header--executive").boundingBox();
  const headingBounds = await page.getByRole("heading", { name: /facilitation comes first/i }).boundingBox();

  expect(headerBounds).not.toBeNull();
  expect(headingBounds).not.toBeNull();
  expect(headingBounds?.y ?? 0).toBeGreaterThanOrEqual((headerBounds?.height ?? 0) + 8);
});

test("public-site supporting copy meets the readability floor", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");

  const sizes = await page.evaluate(() => {
    const lifecycleCopy = document.querySelector(".continuity-grid article p");
    const foundationCopy = document.querySelector(".use-case-grid .use-case p");
    const trustCopy = document.querySelector(".trust-list--executive article span");
    const px = (element: Element | null) => element ? Number.parseFloat(getComputedStyle(element).fontSize) : 0;
    return { lifecycle: px(lifecycleCopy), foundation: px(foundationCopy), trust: px(trustCopy) };
  });

  expect(sizes.lifecycle).toBeGreaterThanOrEqual(16);
  expect(sizes.foundation).toBeGreaterThanOrEqual(16);
  expect(sizes.trust).toBeGreaterThanOrEqual(14);
});

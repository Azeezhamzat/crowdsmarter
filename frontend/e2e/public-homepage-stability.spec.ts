import { expect, test } from "@playwright/test";

const viewports = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "tablet", width: 834, height: 1112 },
  { name: "mobile", width: 390, height: 844 },
];

for (const viewport of viewports) {
  test(`homepage illustrations remain visible at ${viewport.name} width`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /move from emerging change to better judgement/i })).toBeVisible();
    await expect(page.getByRole("img", { name: /signal sensing workflow/i })).toBeVisible();
    await expect(page.getByRole("img", { name: /foresight-to-decision trace/i })).toBeVisible();

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);

    const illustrationBounds = await page.getByRole("img", { name: /signal sensing workflow/i }).boundingBox();
    expect(illustrationBounds).not.toBeNull();
    expect(illustrationBounds?.x ?? -1).toBeGreaterThanOrEqual(0);
    expect((illustrationBounds?.x ?? 0) + (illustrationBounds?.width ?? 0)).toBeLessThanOrEqual(viewport.width + 1);
  });
}

test("each workflow stage has a distinct meaningful illustration", async ({ page }) => {
  await page.goto("/");

  const stages = [
    ["Sense", /signal sensing workflow/i],
    ["Interpret", /systems and scenario interpretation/i],
    ["Decide", /integrated option comparison/i],
    ["Act", /accountable action roadmap/i],
    ["Learn", /organisational learning loop/i],
  ] as const;

  for (const [tabName, illustrationName] of stages) {
    await page.getByRole("tab", { name: new RegExp(tabName, "i") }).click();
    await expect(page.getByRole("img", { name: illustrationName })).toBeVisible();
  }
});


test("sticky navigation does not cover anchored section headings", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "How it works" }).click();

  const headerBounds = await page.locator(".public-header--executive").boundingBox();
  const headingBounds = await page.getByRole("heading", { name: /move from emerging change to better judgement/i }).boundingBox();

  expect(headerBounds).not.toBeNull();
  expect(headingBounds).not.toBeNull();
  expect(headingBounds?.y ?? 0).toBeGreaterThanOrEqual((headerBounds?.height ?? 0) + 8);
});

test("public-site supporting copy meets the readability floor", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");

  const sizes = await page.evaluate(() => {
    const workflowCopy = document.querySelector(".workflow-feature--executive p:not(.public-eyebrow)");
    const capabilityCopy = document.querySelector(".product-capability-grid--executive .product-capability p");
    const traceCaption = document.querySelector(".capability-trace-graphic figcaption");
    const px = (element: Element | null) => element ? Number.parseFloat(getComputedStyle(element).fontSize) : 0;
    return { workflow: px(workflowCopy), capability: px(capabilityCopy), trace: px(traceCaption) };
  });

  expect(sizes.workflow).toBeGreaterThanOrEqual(17);
  expect(sizes.capability).toBeGreaterThanOrEqual(16);
  expect(sizes.trace).toBeGreaterThanOrEqual(13);
});

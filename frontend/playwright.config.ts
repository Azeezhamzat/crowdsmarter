import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  // Against the Vite dev server (not a production build), concurrent workers
  // can each request a different lazy-loaded route chunk for the first time
  // at once; the dev server transforms modules on demand, and under CI's
  // constrained CPU that race intermittently loses ("Failed to fetch
  // dynamically imported module"). Serializing in CI avoids the race.
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});

import type {} from "vitest/config";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { defaultExclude } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // These only ever get imported from inside lazy-loaded route chunks
    // (form pages), never from the eager entry chunk, so Vite's cold-start
    // dependency scan never finds them. Discovering them mid-navigation
    // instead forces a dep re-bundle and a full-page reload while that
    // route's own dynamic import is still in flight, which the browser
    // reports as "Failed to fetch dynamically imported module" for
    // whichever route triggered it. Listing them here pre-bundles them
    // up front instead.
    include: ["zod", "react-hook-form", "@hookform/resolvers/zod"],
  },
  server: {
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
    watch: {
      // Playwright writes its own report/results into this bind-mounted
      // directory during e2e runs; without this, Vite treats those writes
      // as source changes and reloads the page mid-navigation, aborting
      // any in-flight lazy-loaded route import.
      ignored: ["**/playwright-report/**", "**/test-results/**"],
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts",
    globals: true,
    exclude: [...defaultExclude, "e2e/**"],
    // The default 5000ms per-test timeout is tuned for an idle machine;
    // under full-suite parallel load many jsdom environments compete for
    // CPU and a correctly-rendering test can exceed it non-deterministically.
    testTimeout: 15000,
  },
});

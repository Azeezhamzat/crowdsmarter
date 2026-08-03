/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { defaultExclude } from "vitest/config";

export default defineConfig({
  plugins: [react()],
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

import "@testing-library/jest-dom/vitest";
import { configure } from "@testing-library/react";
import { vi } from "vitest";

// The default 1000ms findBy/waitFor timeout is tuned for an idle developer
// machine. Under full-suite parallel load (many jsdom environments and React
// Query resolutions running concurrently) correctly-rendering components can
// exceed it non-deterministically, producing flaky failures unrelated to any
// real defect. A longer ceiling keeps genuinely broken renders failing while
// removing that timing flakiness.
configure({ asyncUtilTimeout: 5000 });

// jsdom deliberately leaves media playback unimplemented. Stub the browser
// contract so components can exercise their play/pause state without noisy,
// environment-only errors in otherwise successful tests.
Object.defineProperty(HTMLMediaElement.prototype, "play", {
  configurable: true,
  value: vi.fn().mockResolvedValue(undefined),
});
Object.defineProperty(HTMLMediaElement.prototype, "pause", {
  configurable: true,
  value: vi.fn(),
});

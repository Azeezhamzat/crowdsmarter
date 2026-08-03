import "@testing-library/jest-dom/vitest";
import { configure } from "@testing-library/react";

// The default 1000ms findBy/waitFor timeout is tuned for an idle developer
// machine. Under full-suite parallel load (many jsdom environments and React
// Query resolutions running concurrently) correctly-rendering components can
// exceed it non-deterministically, producing flaky failures unrelated to any
// real defect. A longer ceiling keeps genuinely broken renders failing while
// removing that timing flakiness.
configure({ asyncUtilTimeout: 5000 });

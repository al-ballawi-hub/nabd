import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Ensure the DOM is cleaned between tests (RTL auto-cleanup relies on a
// global afterEach, which is unavailable without Vitest globals).
afterEach(() => {
  cleanup();
});

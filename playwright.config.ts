import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for MIR'S END e2e tests.
 *
 * The tests drive a real browser against a local static server serving `game/`.
 * Playwright manages the server lifecycle via `webServer` below.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:8181",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "python3 -m http.server 8181 --directory game",
    url: "http://localhost:8181/play.html",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});

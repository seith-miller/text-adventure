import { expect, test } from "@playwright/test";
import {
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

const _CANNED_LINE =
  "You key the channel for Argon-87. No response. The runtime is not attached this watch.";
const _AI_ONBOARDING_KEY = "mirsend_ai_onboarding_seen";

test.describe("ai-feature-flag — flag OFF (default)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("TALK TO ARGON prints the canned line and does not crash", async ({
    page,
  }) => {
    await startNewGame(page);

    // Verify AI is off by default
    const aiEnabled = await page.evaluate(
      () => (window as any).MirsEnd.config.aiEnabled,
    );
    expect(aiEnabled).toBe(false);

    await sendCommand(page, "talk to argon");
    await waitForStoryText(page, "runtime is not attached");

    const text = await storyText(page);
    expect(text).toContain("runtime is not attached");
  });

  test("SPEAK TO ARGON also prints the canned line", async ({ page }) => {
    await startNewGame(page);

    await sendCommand(page, "speak to argon");
    await waitForStoryText(page, "runtime is not attached");
  });

  test("ASK ARGON prints the canned line", async ({ page }) => {
    await startNewGame(page);

    await sendCommand(page, "ask argon");
    await waitForStoryText(page, "runtime is not attached");
  });

  test("no AI online badge is visible when flag is off", async ({ page }) => {
    await startNewGame(page);

    const badge = page.locator("#ai-status-badge");
    await expect(badge).toHaveCount(0);
  });

  test("no onboarding modal appears when flag is off", async ({ page }) => {
    await startNewGame(page);

    const overlay = page.locator("#ai-onboarding-overlay");
    await expect(overlay).toHaveCount(0);
  });

  test("config.aiEnabled is false by default", async ({ page }) => {
    await startNewGame(page);

    const config = await page.evaluate(() => (window as any).MirsEnd.config);
    expect(config.aiEnabled).toBe(false);
  });
});

test.describe("ai-feature-flag — flag ON", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
    // Enable the AI flag before the UI shell reads it
    await page.evaluate(() => {
      (window as any).MIRSEND_AI_ENABLED = 1;
    });
    // Reload so ui.js picks up the flag
    await page.evaluate(() => {
      (window as any).MIRSEND_AI_ENABLED = 1;
    });
  });

  test("config.aiEnabled is true when flag is set before load", async ({
    page,
  }) => {
    // We need to set the flag BEFORE ui.js runs, so use addInitScript
    await page.addInitScript(() => {
      (window as any).MIRSEND_AI_ENABLED = 1;
    });
    await page.goto("/play.html");
    await clearStorage(page);

    const aiEnabled = await page.evaluate(
      () => (window as any).MirsEnd.config.aiEnabled,
    );
    expect(aiEnabled).toBe(true);
  });

  test("AI online badge is visible when flag is on", async ({ page }) => {
    await page.addInitScript(() => {
      (window as any).MIRSEND_AI_ENABLED = 1;
    });
    await page.goto("/play.html");

    const badge = page.locator("#ai-status-badge");
    await expect(badge).toBeVisible();
    await expect(badge).toHaveText("AI online");
  });

  test("first-run onboarding modal appears once", async ({ page }) => {
    await page.addInitScript(() => {
      (window as any).MIRSEND_AI_ENABLED = 1;
    });
    await page.goto("/play.html");
    await clearStorage(page);
    // Reload to trigger fresh onboarding
    await page.goto("/play.html");

    const overlay = page.locator("#ai-onboarding-overlay");
    await expect(overlay).toBeVisible();

    // Dismiss it
    await page.click("#ai-onboarding-dismiss");
    await expect(overlay).toHaveCount(0);

    // Reload — should NOT appear again
    await page.goto("/play.html");
    const overlayAgain = page.locator("#ai-onboarding-overlay");
    await expect(overlayAgain).toHaveCount(0);
  });

  test("TALK TO ARGON with proxy down prints canned line and logs outage", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      (window as any).MIRSEND_AI_ENABLED = 1;
      // Suppress the first-run onboarding modal so it does not intercept
      // clicks on the title screen during this test.
      try {
        localStorage.setItem("mirsend_ai_onboarding_seen", "1");
      } catch (_e) {
        /* localStorage may be unavailable */
      }
    });

    // Collect console warnings
    const warnings: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "warning") warnings.push(msg.text());
    });

    await startNewGame(page);

    await sendCommand(page, "talk to argon");
    // Proxy is not running in test environment — should fall back
    await waitForStoryText(page, "runtime is not attached");

    // Verify the outage was logged
    expect(warnings.some((w) => w.includes("proxy unreachable"))).toBe(true);
  });
});

/**
 * Optional typing / decode-in effect on new story text (m13 #140).
 *
 * Validates the five acceptance criteria from the issue:
 *
 *   1. Configurable speed (chars/sec) and on/off toggle
 *   2. Skippable per-message with any key
 *   3. Doesn't break scrolling or existing rendering
 *   4. Default off — opt-in
 *   5. Doesn't slow gameplay perceptibly (queue drains after skip)
 *
 * Drives `window.MirsEnd` directly so tests exercise the renderer
 * without spinning up the full Glulx interpreter.
 */

import { expect, test } from "@playwright/test";

const TYPING_STORAGE_KEY = "mirsend_typing_settings";

test.describe("typing-effect — default off", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.getTypingConfig !== undefined,
    );
  });

  test("typing effect is OFF by default", async ({ page }) => {
    const cfg = await page.evaluate(() =>
      (window as any).MirsEnd.getTypingConfig(),
    );
    expect(cfg.enabled).toBe(false);
  });

  test("a default config exposes a charsPerSec speed", async ({ page }) => {
    const cfg = await page.evaluate(() =>
      (window as any).MirsEnd.getTypingConfig(),
    );
    expect(typeof cfg.charsPerSec).toBe("number");
    expect(cfg.charsPerSec).toBeGreaterThan(0);
  });

  test("with effect off, full text is rendered immediately", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "The phosphor catches your breath.",
      ),
    );
    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("The phosphor catches your breath.");
  });
});

test.describe("typing-effect — turned on", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.setTypingConfig !== undefined,
    );
  });

  test("setTypingConfig({enabled:true}) flips the toggle", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({ enabled: true }),
    );
    const cfg = await page.evaluate(() =>
      (window as any).MirsEnd.getTypingConfig(),
    );
    expect(cfg.enabled).toBe(true);
  });

  test("typing-config persists to localStorage", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 42,
      }),
    );
    const raw = await page.evaluate(
      (k) => localStorage.getItem(k),
      TYPING_STORAGE_KEY,
    );
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw as string);
    expect(parsed.enabled).toBe(true);
    expect(parsed.charsPerSec).toBe(42);
  });

  test("typing-config reloads from localStorage on next visit", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 33,
      }),
    );
    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.getTypingConfig !== undefined,
    );
    const cfg = await page.evaluate(() =>
      (window as any).MirsEnd.getTypingConfig(),
    );
    expect(cfg.enabled).toBe(true);
    expect(cfg.charsPerSec).toBe(33);
  });

  test("with effect on at a slow speed, text appears progressively", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 30,
      }),
    );
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "Slowly the words appear in the dim phosphor glow above the bunk.",
      ),
    );
    // Right after kickoff, the full payload should NOT yet be on screen.
    const earlyDisplay = (await page.locator("#display").textContent()) ?? "";
    expect(earlyDisplay).not.toContain(
      "the dim phosphor glow above the bunk.",
    );
    // After the animation completes, the full text must be visible.
    await page.waitForFunction(
      () =>
        ((document.querySelector("#display") as HTMLElement)?.textContent ?? "")
          .indexOf("the dim phosphor glow above the bunk.") !== -1,
      undefined,
      { timeout: 5000 },
    );
  });

  test("skipTyping() reveals the full message immediately", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 5,
      }),
    );
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "A long line of text that would otherwise take many seconds to fully render.",
      ),
    );
    await page.evaluate(() => (window as any).MirsEnd.skipTyping());
    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("would otherwise take many seconds");
  });

  test("pressing a key during animation triggers skip", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 5,
      }),
    );
    // Mark gameStarted so the document-level keydown handler arms.
    await page.evaluate(() => {
      const s = (window as any).MirsEnd.getState();
      s.gameStarted = true;
    });
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "A long line of text that would otherwise take many seconds to fully render.",
      ),
    );
    await page.keyboard.press("Space");
    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("would otherwise take many seconds");
  });

  test("queued message drains after the active one is skipped", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 5,
      }),
    );
    await page.evaluate(() => {
      const M = (window as any).MirsEnd;
      M.appendStoryText("First message arrives slowly into the buffer.");
      M.appendStoryText("BEACON_TWO follows right behind it.");
    });
    // Skip twice — once for each queued payload.
    await page.evaluate(() => (window as any).MirsEnd.skipTyping());
    await page.evaluate(() => (window as any).MirsEnd.skipTyping());
    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("BEACON_TWO");
  });

  test("scrolling still works while a typing animation is active", async ({
    page,
  }) => {
    // Fill the buffer first so there is something to scroll over.
    await page.evaluate(() => {
      const M = (window as any).MirsEnd;
      for (let i = 0; i < 60; i++) {
        M.appendStoryText(`History line ${i} of the prior buffer.`);
      }
    });
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingConfig({
        enabled: true,
        charsPerSec: 5,
      }),
    );
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "A new long line of phosphor text typing slowly into the buffer.",
      ),
    );
    await page.evaluate(() => (window as any).MirsEnd.scrollUp(5));
    const offset = await page.evaluate(() =>
      (window as any).MirsEnd.getScrollOffset(),
    );
    expect(offset).toBeGreaterThan(0);
    // Skip and confirm scroll state was preserved (still scrolled up).
    await page.evaluate(() => (window as any).MirsEnd.skipTyping());
    const offsetAfter = await page.evaluate(() =>
      (window as any).MirsEnd.getScrollOffset(),
    );
    expect(offsetAfter).toBeGreaterThan(0);
  });
});

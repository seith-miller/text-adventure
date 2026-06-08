/**
 * Typing / decode-in effect (m13 #140).
 *
 * Tests the optional character-reveal animation on new story text.
 * Exercises:
 *   - default OFF (text appears instantly)
 *   - typing mode: progressive character reveal
 *   - decode mode: random glyphs settle into final text
 *   - skip on keypress
 *   - settings API (get/set/persist)
 *   - scrolling not broken during animation
 */

import { expect, test } from "@playwright/test";

/** Helper: wait for MirsEnd API to be ready. */
async function waitForApi(page: import("@playwright/test").Page) {
  await page.goto("/play.html");
  await page.waitForFunction(
    () =>
      (window as any).MirsEnd?.appendStoryText !== undefined &&
      (window as any).MirsEnd?.setTypingEffect !== undefined,
  );
}

test.describe("typing effect", () => {
  test.beforeEach(async ({ page }) => {
    await waitForApi(page);
  });

  test("is disabled by default — text appears instantly", async ({ page }) => {
    const settings = await page.evaluate(() =>
      (window as any).MirsEnd.getTypingEffect(),
    );
    expect(settings.enabled).toBe(false);

    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText("Instant text check."),
    );

    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("Instant text check.");

    const active = await page.evaluate(() =>
      (window as any).MirsEnd.isTypingActive(),
    );
    expect(active).toBe(false);
  });

  test("typing mode reveals text progressively", async ({ page }) => {
    // Enable typing at a moderate speed so we can catch the mid-animation state
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 15,
        mode: "typing",
      }),
    );

    const testText = "The reactor hums beneath the deck plates.";
    await page.evaluate(
      (t) => (window as any).MirsEnd.appendStoryText(t),
      testText,
    );

    // Animation should be active
    const active = await page.evaluate(() =>
      (window as any).MirsEnd.isTypingActive(),
    );
    expect(active).toBe(true);

    // The full text should NOT be visible yet (15 chars/sec, ~40 chars = ~2.7s)
    const displayMid = (await page.locator("#display").textContent()) ?? "";
    expect(displayMid).not.toContain(testText);

    // Skip the animation
    await page.evaluate(() => (window as any).MirsEnd.skipTypingEffect());

    // Now the full text should be visible
    const displayAfter = (await page.locator("#display").textContent()) ?? "";
    expect(displayAfter).toContain(testText);
  });

  test("decode mode shows random glyphs that settle into final text", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 10,
        mode: "decode",
      }),
    );

    const testText = "Argon whispers from the console.";
    await page.evaluate(
      (t) => (window as any).MirsEnd.appendStoryText(t),
      testText,
    );

    // Animation should be active
    const active = await page.evaluate(() =>
      (window as any).MirsEnd.isTypingActive(),
    );
    expect(active).toBe(true);

    // Skip to completion
    await page.evaluate(() => (window as any).MirsEnd.skipTypingEffect());

    const displayAfter = (await page.locator("#display").textContent()) ?? "";
    expect(displayAfter).toContain(testText);
  });

  test("any keypress skips the animation", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 5,
        mode: "typing",
      }),
    );

    const testText = "A warning klaxon echoes through the module.";
    await page.evaluate(
      (t) => (window as any).MirsEnd.appendStoryText(t),
      testText,
    );

    // Verify animation is running
    const activeBefore = await page.evaluate(() =>
      (window as any).MirsEnd.isTypingActive(),
    );
    expect(activeBefore).toBe(true);

    // Press a key to skip
    await page.keyboard.press("Space");

    // Give a frame for the keydown handler to fire
    await page.waitForTimeout(50);

    const activeAfter = await page.evaluate(() =>
      (window as any).MirsEnd.isTypingActive(),
    );
    expect(activeAfter).toBe(false);

    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain(testText);
  });

  test("settings API roundtrips correctly", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 42,
        mode: "decode",
      }),
    );

    const settings = await page.evaluate(() =>
      (window as any).MirsEnd.getTypingEffect(),
    );
    expect(settings.enabled).toBe(true);
    expect(settings.speed).toBe(42);
    expect(settings.mode).toBe("decode");
  });

  test("settings persist in localStorage", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 25,
        mode: "typing",
      }),
    );

    const stored = await page.evaluate(() =>
      JSON.parse(localStorage.getItem("mirsend_typing_effect") ?? "{}"),
    );
    expect(stored.enabled).toBe(true);
    expect(stored.speed).toBe(25);
    expect(stored.mode).toBe("typing");
  });

  test("scrolling still works during animation", async ({ page }) => {
    // Fill buffer so scrollback is meaningful
    await page.evaluate(() => {
      const M = (window as any).MirsEnd;
      for (let i = 0; i < 40; i++) {
        M.appendStoryText(`Buffer line ${i}.`);
      }
    });

    // Enable typing effect
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 10,
        mode: "typing",
      }),
    );

    // Append new text (will animate)
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "This line is being typed slowly.",
      ),
    );

    // Scroll up while animation is in progress
    await page.evaluate(() => (window as any).MirsEnd.scrollUp(5));
    const offset = await page.evaluate(() =>
      (window as any).MirsEnd.getScrollOffset(),
    );
    expect(offset).toBeGreaterThan(0);

    // Skip and verify text is there when scrolled to bottom
    await page.evaluate(() => (window as any).MirsEnd.skipTypingEffect());
    await page.evaluate(() => (window as any).MirsEnd.scrollToBottom());

    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("This line is being typed slowly.");
  });

  test("multiple queued texts are all revealed after skip", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 5,
        mode: "typing",
      }),
    );

    // Queue multiple text blocks rapidly
    await page.evaluate(() => {
      const M = (window as any).MirsEnd;
      M.appendStoryText("First message from the station.");
      M.appendStoryText("Second message arrives quickly.");
    });

    // Skip all
    await page.evaluate(() => (window as any).MirsEnd.skipTypingEffect());

    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("First message from the station.");
    expect(display).toContain("Second message arrives quickly.");
  });

  test("typing completes naturally at high speed", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.setTypingEffect({
        enabled: true,
        speed: 1000,
        mode: "typing",
      }),
    );

    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText("Quick reveal test."),
    );

    // At 1000 chars/sec a short string finishes near-instantly
    await page.waitForTimeout(200);

    const active = await page.evaluate(() =>
      (window as any).MirsEnd.isTypingActive(),
    );
    expect(active).toBe(false);

    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("Quick reveal test.");
  });
});

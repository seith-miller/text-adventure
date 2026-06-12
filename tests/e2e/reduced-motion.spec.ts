import { expect, test } from "@playwright/test";
import { clearStorage } from "./helpers";

/**
 * Reduced-motion accessibility (#144).
 *
 * Three modes — auto (follow OS), on (force reduced), off (force full).
 * When reduced, `html.reduced-motion` is set, the cursor blink animation
 * stops, the scanline element hides, button transitions snap.
 */

test.describe("reduced-motion", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("default mode is auto and follows OS preference (reduced)", async ({
    browser,
  }) => {
    /* Fresh context with prefers-reduced-motion: reduce emulated. */
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    await expect(page.locator("html")).toHaveClass(/reduced-motion/);
    const mode = await page.evaluate(() =>
      (window as any).MirsEndMotion.getMode(),
    );
    expect(mode).toBe("auto");
    await ctx.close();
  });

  test("default mode is auto and follows OS preference (no-preference)", async ({
    browser,
  }) => {
    const ctx = await browser.newContext({ reducedMotion: "no-preference" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    await expect(page.locator("html")).not.toHaveClass(/reduced-motion/);
    await ctx.close();
  });

  test('setMode("on") forces reduced-motion class even when OS prefers full motion', async ({
    browser,
  }) => {
    const ctx = await browser.newContext({ reducedMotion: "no-preference" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    await expect(page.locator("html")).not.toHaveClass(/reduced-motion/);
    await page.evaluate(() => (window as any).MirsEndMotion.setMode("on"));
    await expect(page.locator("html")).toHaveClass(/reduced-motion/);
    await ctx.close();
  });

  test('setMode("off") forces full motion even when OS prefers reduced', async ({
    browser,
  }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    await expect(page.locator("html")).toHaveClass(/reduced-motion/);
    await page.evaluate(() => (window as any).MirsEndMotion.setMode("off"));
    await expect(page.locator("html")).not.toHaveClass(/reduced-motion/);
    await ctx.close();
  });

  test("mode persists in localStorage across reloads", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "no-preference" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    await page.evaluate(() => (window as any).MirsEndMotion.setMode("on"));
    await page.reload();
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    await expect(page.locator("html")).toHaveClass(/reduced-motion/);
    const mode = await page.evaluate(() =>
      (window as any).MirsEndMotion.getMode(),
    );
    expect(mode).toBe("on");
    await ctx.close();
  });

  test("Settings button opens the Settings modal and cycles modes", async ({
    page,
  }) => {
    /* Settings button is enabled by reduced-motion.js init. */
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    const settingsBtn = page.locator("#menu-settings");
    await expect(settingsBtn).toBeEnabled();
    await settingsBtn.click();

    const modal = page.locator("#settings-modal");
    await expect(modal).toBeVisible();

    const valueBtn = page.locator("#settings-reduced-motion");
    /* Default is "auto". Cycle → on → off → auto. */
    await expect(valueBtn).toContainText("AUTO");
    await valueBtn.click();
    await expect(valueBtn).toContainText("ON");
    await valueBtn.click();
    await expect(valueBtn).toContainText("OFF");
    await valueBtn.click();
    await expect(valueBtn).toContainText("AUTO");

    await page.locator("#settings-close").click();
    await expect(page.locator("#settings-overlay")).toHaveCount(0);
  });

  test("scanline element is hidden when reduced-motion is active", async ({
    browser,
  }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    const scanline = page.locator("#scan-line");
    await expect(scanline).toBeHidden();
    await ctx.close();
  });

  test("cursor animation is suppressed when reduced-motion is active", async ({
    browser,
  }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await page.goto("/play.html");
    await page.waitForFunction(() => !!(window as any).MirsEndMotion);
    /* The <cur> tag exists inside the rendered display grid. */
    const animation = await page.evaluate(() => {
      const cur = document.querySelector("cur");
      if (!cur) return null;
      return window.getComputedStyle(cur).animationName;
    });
    expect(animation === "none" || animation === null).toBe(true);
    await ctx.close();
  });
});

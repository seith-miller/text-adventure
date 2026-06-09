/**
 * CRT input polish (m13 #133).
 *
 * Verifies the three input-row refinements from the issue:
 *
 *   1. Typed text renders in <bri> phosphor with blinking █ cursor
 *   2. Enter echoes `> command` into the story column as <echo>
 *   3. Command history persists across sessions via localStorage
 */

import { expect, test } from "@playwright/test";
import { clearStorage, readStorage } from "./helpers";

const HISTORY_KEY = "mirsend_command_history";

test.describe("CRT input polish", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("typed text appears inside <bri> tags in the display", async ({
    page,
  }) => {
    await page.waitForFunction(
      () => (window as any).MirsEnd?.appendStoryText !== undefined,
    );

    const cmdInput = page.locator("#command-input");
    await cmdInput.focus();
    await cmdInput.fill("look around");
    // Allow handleInputChange to fire and renderDisplay to update
    await page.waitForTimeout(100);

    const html = await page.locator("#display").innerHTML();
    // The typed text "look around" should be wrapped in <bri> tags
    expect(html).toContain("<bri>look around</bri>");
  });

  test("blinking █ cursor is rendered with <cur> tag", async ({ page }) => {
    await page.waitForFunction(
      () => (window as any).MirsEnd?.appendStoryText !== undefined,
    );

    const html = await page.locator("#display").innerHTML();
    // Cursor should always be visible in the input row
    expect(html).toContain("<cur>█</cur>");
  });

  test("Enter echoes command as <echo> in story column", async ({ page }) => {
    await page.waitForFunction(
      () => (window as any).MirsEnd?.appendStoryText !== undefined,
    );

    await page.evaluate(() =>
      (window as any).MirsEnd.appendPlayerInput("examine console"),
    );
    const html = await page.locator("#display").innerHTML();
    expect(html).toContain("<echo>&gt; examine console</echo>");
  });

  test("command history is saved to localStorage on Enter", async ({
    page,
  }) => {
    await page.waitForFunction(
      () => (window as any).MirsEnd?.appendStoryText !== undefined,
    );

    const cmdInput = page.locator("#command-input");
    await cmdInput.focus();
    await cmdInput.fill("look");
    await cmdInput.press("Enter");
    await page.waitForTimeout(100);

    await cmdInput.fill("north");
    await cmdInput.press("Enter");
    await page.waitForTimeout(100);

    const stored = await readStorage(page, HISTORY_KEY);
    expect(stored).not.toBeNull();
    const history = JSON.parse(stored!);
    expect(history).toContain("look");
    expect(history).toContain("north");
  });

  test("command history is restored from localStorage on page load", async ({
    page,
  }) => {
    // Seed history into localStorage before loading
    const seedHistory = JSON.stringify(["inventory", "go east"]);
    await page.evaluate(
      ([key, val]) => localStorage.setItem(key, val),
      [HISTORY_KEY, seedHistory],
    );

    // Reload to pick up the seeded history
    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.getState !== undefined,
    );

    const state = await page.evaluate(() => (window as any).MirsEnd.getState());
    expect(state.commandHistory).toContain("inventory");
    expect(state.commandHistory).toContain("go east");
  });

  test("up arrow recalls command from persisted history", async ({ page }) => {
    // Seed history
    const seedHistory = JSON.stringify(["open locker", "take flashlight"]);
    await page.evaluate(
      ([key, val]) => localStorage.setItem(key, val),
      [HISTORY_KEY, seedHistory],
    );

    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.getState !== undefined,
    );

    const cmdInput = page.locator("#command-input");
    await cmdInput.focus();
    await cmdInput.press("ArrowUp");

    const value = await cmdInput.inputValue();
    expect(value).toBe("take flashlight");
  });
});

import { expect, test } from "@playwright/test";
import { clearStorage, startNewGame, storyText } from "./helpers";

/**
 * This test drives the VISIBLE #command-input — the path a real player
 * uses. It's intentionally distinct from helpers.sendCommand (which
 * bypasses ui.js and types directly into GlkOte's LineInput for speed).
 *
 * If ui.js.sendToInterpreter ever silently stops forwarding input to
 * the interpreter again, this test will catch it.
 */
test.describe("user-input-reaches-interpreter", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("typing into #command-input produces an interpreter response", async ({
    page,
  }) => {
    await startNewGame(page);

    const cmdInput = page.locator("#command-input");
    await cmdInput.focus();
    await cmdInput.fill("open emergency locker");
    await cmdInput.press("Enter");
    await page.waitForTimeout(800);

    const story = await storyText(page);
    expect(story).toMatch(/revealing a flashlight/i);
  });

  test("multiple commands in a row each get responses", async ({ page }) => {
    await startNewGame(page);
    const cmdInput = page.locator("#command-input");

    const commands = ["open emergency locker", "take chemical flashlight"];
    for (const cmd of commands) {
      await cmdInput.focus();
      await cmdInput.fill(cmd);
      await cmdInput.press("Enter");
      await page.waitForTimeout(600);
    }

    const story = await storyText(page);
    expect(story).toMatch(/revealing a flashlight/i);
    expect(story).toMatch(/Taken/i);
  });
});

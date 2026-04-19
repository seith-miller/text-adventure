import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

test.describe("ui-status-mirrors-game", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("o2 ticks down every turn", async ({ page }) => {
    await startNewGame(page);
    const before = (await asMirsEnd(page)).o2;
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await asMirsEnd(page)).o2, { timeout: 3_000 })
      .toBeLessThan(before);
  });

  test("morale jumps when lighting the flashlight", async ({ page }) => {
    await startNewGame(page);
    /* Let at least one status line land so baseline reflects the Inform-side
       value (which is 50, not the ui.js default of 70). */
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await asMirsEnd(page)).morale, { timeout: 3_000 })
      .toBe(50);

    const baseline = (await asMirsEnd(page)).morale;
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker/i);
    await sendCommand(page, "take chemical flashlight");
    await waitForStoryText(page, /Taken/i);
    await sendCommand(page, "switch on chemical flashlight");
    await waitForStoryText(page, /green|glow/i);
    /* +5 morale from the flashlight Instead rule; morale doesn't decay per
       turn (only oxygen does), so the bump should be observable. */
    await expect
      .poll(async () => (await asMirsEnd(page)).morale, { timeout: 3_000 })
      .toBeGreaterThan(baseline);
  });

  test("inventory shows items the player is actually carrying", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker|Zhuchok/i);
    // Object accepts "zhuchok", "torch", "flashlight" as synonyms.
    await sendCommand(page, "take zhuchok");
    await waitForStoryText(page, /Taken/i);
    await expect
      .poll(async () => (await asMirsEnd(page)).inventory.join(","), {
        timeout: 3_000,
      })
      .toMatch(/Zhuchok/i);
  });

  test("the machine-readable status line is suppressed from the visible panel", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "look");
    await page.waitForTimeout(500);
    const visible = await storyText(page);
    expect(visible).not.toMatch(/\[MIRSEND/);
  });
});

import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

/**
 * E5 passive-failure denouement tests.
 *
 * - A passive player (no climax committed) eventually suffocates via E5.
 * - A player who transmits (C1 climax) does NOT suffocate; the oxygen
 *   timer is guarded and the scripted arc handles termination.
 */

test.describe("e5-timer-guard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("passive playthrough ends with E5 placeholder when oxygen runs out", async ({
    page,
  }) => {
    // 110 turns × 100ms wait + sendCommand overhead lands around 30-40s
    // on CI. Playwright silently ignores `timeout` in the test-details
    // arg; setTimeout in the body is the documented per-test override.
    test.setTimeout(180_000);
    await startNewGame(page);

    // The player does nothing meaningful — just waits until O2 hits 0.
    // O2 starts at 100 and decreases by 1 per turn, so we need ~100 waits.
    // startNewGame already consumed a couple of turns.
    for (let i = 0; i < 110; i++) {
      await sendCommand(page, "wait");
      // Small pause to let the interpreter catch up
      await page.waitForTimeout(100);
    }

    // The E5 dispatcher should have fired with the placeholder text
    const text = await storyText(page);
    expect(text).toMatch(/TODO prose: #60/i);
    expect(text).toMatch(/suffocated/i);
  });

  test("player who transmits does NOT suffocate — climax guard stops O2 drain", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    await startNewGame(page);

    // Full walkthrough to TRANSMIT (C1 climax commitment)
    const walkthrough = [
      "open emergency locker",
      "take chemical flashlight",
      "switch on chemical flashlight",
      "listen",
      "pull lever",
      "north", // Main Corridor
      "examine yevgenia",
      "take notebook",
      "read notebook",
      "east", // fails — armament bay locked
      "examine viewport", // fails — not in cupola
      "down", // Observation Cupola
      "examine viewport",
      "examine petrov",
      "up", // Main Corridor
      "north", // Command Module
      "open toolkit",
      "take multimeter",
      "restore power",
      "read log",
      "listen", // hear distress call
      "transmit", // C1 climax — responded-to-americans is now true
    ];

    for (const cmd of walkthrough) {
      await sendCommand(page, cmd);
      await page.waitForTimeout(200);
    }

    await waitForStoryText(page, /Begin preparations/i);

    // Now record O2 level after climax commitment
    const o2After = (await asMirsEnd(page)).o2;

    // Send several more turns — O2 should NOT decrease
    for (let i = 0; i < 10; i++) {
      await sendCommand(page, "wait");
      await page.waitForTimeout(100);
    }

    const o2Later = (await asMirsEnd(page)).o2;
    // O2 should be unchanged since the guard prevents depletion
    expect(o2Later).toBe(o2After);

    // And the suffocation text should NOT appear
    const text = await storyText(page);
    expect(text).not.toMatch(/suffocated/i);
  });
});

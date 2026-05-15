import { expect, test } from "@playwright/test";
import {
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

/**
 * C2 Descend mechanics: DEORBIT action → D3 reentry → E3 return.
 *
 * Covers the full descent arc from Soyuz Ferry through six scripted
 * reentry beats to the terminal E3 ending.
 */

/** Run minimal Act 1 to reach Main Corridor. */
async function minimalAct1(page: import("@playwright/test").Page) {
  await startNewGame(page);
  await sendCommand(page, "open emergency locker");
  await waitForStoryText(page, /flashlight|locker/i);
  await sendCommand(page, "take flashlight");
  await waitForStoryText(page, /Taken/i);
  await sendCommand(page, "switch on flashlight");
  await waitForStoryText(page, /yellow|beetle/i);
  await sendCommand(page, "pull lever");
  await waitForStoryText(page, /hiss|equalize/i);
  await sendCommand(page, "n");
  await waitForStoryText(page, /Main Corridor|central node/i);
}

/** Complete 3+ B1 beats: notebook read, power restore, log read. */
async function completeBeatGate(page: import("@playwright/test").Page) {
  // Take and read notebook (B1 beat 1)
  await sendCommand(page, "take notebook");
  await waitForStoryText(page, /unclip|notebook/i);
  await sendCommand(page, "read notebook");
  await waitForStoryText(page, /EMP confirmed|Selengrad/i);
  // Go to Command Module
  await sendCommand(page, "n");
  await waitForStoryText(page, /command module|control panels/i);
  // Get multimeter
  await sendCommand(page, "open toolkit");
  await waitForStoryText(page, /open/i);
  await sendCommand(page, "take multimeter");
  await waitForStoryText(page, /Taken/i);
  // Restore power (B1 beat 2)
  await sendCommand(page, "restore power");
  await waitForStoryText(page, /console flickers|sparks/i);
  // Read log (B1 beat 3)
  await sendCommand(page, "read log");
  await waitForStoryText(page, /Commander Vasili Petrov|EMP event confirmed/i);
}

/** Navigate from Command Module to Soyuz Ferry. */
async function enterSoyuz(page: import("@playwright/test").Page) {
  await sendCommand(page, "e");
  await waitForStoryText(page, /Soyuz|descent module/i);
}

test.describe("c2-descent", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("DEORBIT triggers six-beat D3 sequence then E3 ending", async ({
    page,
  }) => {
    // A → Main Corridor
    await minimalAct1(page);
    // Complete 3 B1 beats
    await completeBeatGate(page);
    // Enter Soyuz
    await enterSoyuz(page);

    // Trigger DEORBIT
    await sendCommand(page, "deorbit");
    await waitForStoryText(page, /retrorockets|de-orbit sequence/i);

    // The D3 sequence fires one beat per turn. We issue a no-op command
    // ("wait" / "z") each turn to advance the counter.
    // Beat 1: d3-deorbit-burn
    await sendCommand(page, "wait");
    await waitForStoryText(page, /d3-deorbit-burn/i);

    // Beat 2: d3-atmosphere-entry
    await sendCommand(page, "wait");
    await waitForStoryText(page, /d3-atmosphere-entry/i);

    // Beat 3: d3-no-ground-control
    await sendCommand(page, "wait");
    await waitForStoryText(page, /d3-no-ground-control/i);

    // Beat 4: d3-continents-visible
    await sendCommand(page, "wait");
    await waitForStoryText(page, /d3-continents-visible/i);

    // Beat 5: d3-soot-layers
    await sendCommand(page, "wait");
    await waitForStoryText(page, /d3-soot-layers/i);

    // Beat 6: d3-touchdown
    await sendCommand(page, "wait");
    await waitForStoryText(page, /d3-touchdown/i);

    // E3 fires on the next turn — game ends
    await sendCommand(page, "wait");
    await waitForStoryText(page, /e3-return/i);

    // The game should show the ending
    const text = await storyText(page);
    expect(text).toMatch(/You have returned/i);
  });

  test("DEORBIT is blocked when not in Soyuz Ferry", async ({ page }) => {
    await minimalAct1(page);
    await completeBeatGate(page);
    // Still in Command Module, not Soyuz
    await sendCommand(page, "deorbit");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /aboard the Soyuz ferry/i,
    );
  });

  test("DEORBIT is blocked before Act 2 beat gate", async ({ page }) => {
    await minimalAct1(page);
    // Go straight to Soyuz without completing beats
    await sendCommand(page, "n");
    await waitForStoryText(page, /command module|control panels/i);
    await enterSoyuz(page);
    await sendCommand(page, "deorbit");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /not ready to leave|barely begun/i,
    );
  });

  test("DEORBIT is blocked after TRANSMIT (C1 lock)", async ({ page }) => {
    await minimalAct1(page);
    await completeBeatGate(page);
    // Listen and transmit first (C1 path)
    await sendCommand(page, "listen");
    await waitForStoryText(page, /Freedom Station|distress/i);
    await sendCommand(page, "transmit");
    await waitForStoryText(page, /key the microphone|Commander.*Chen/i);
    // Now try to deorbit
    await enterSoyuz(page);
    await sendCommand(page, "deorbit");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /Selengrad plan|de-orbit path is closed/i,
    );
  });

  test("oxygen timer does not fire during descent", async ({ page }) => {
    await minimalAct1(page);
    await completeBeatGate(page);
    await enterSoyuz(page);
    await sendCommand(page, "deorbit");
    await waitForStoryText(page, /retrorockets|de-orbit sequence/i);

    // Advance through all D3 beats — oxygen should never cause
    // suffocation because the timer is guarded by chose-descent.
    for (let i = 0; i < 7; i++) {
      await sendCommand(page, "wait");
    }

    // If we got here without suffocating, the guard works.
    // The game should end with "returned", not "suffocated".
    const text = await storyText(page);
    expect(text).toMatch(/You have returned/i);
    expect(text).not.toMatch(/suffocated/i);
  });
});

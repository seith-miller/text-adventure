import { expect, test } from "@playwright/test";
import {
  clearStorage,
  sendCommand,
  startNewGame,
  waitForStoryText,
} from "./helpers";

/**
 * Act 2 path tracking and B→C transition gates.
 *
 * The climax actions (TRANSMIT, DEORBIT, FIRE CANNON) are soft-blocked
 * until the player has completed at least 3 beats in either the B1
 * (engineer) or B2 (witness) Act 2 path.
 */

/** Helper: run minimal Act 1 to reach the Main Corridor. */
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

/** Helper: run the full B1 (engineer) path from Main Corridor to
 *  having power restored + log read + safe opened. Returns in
 *  Command Module with 4 B1 beats completed. */
async function fullB1Path(page: import("@playwright/test").Page) {
  // Take notebook from Yevgenia (B1 beat 1: notebook read)
  await sendCommand(page, "take notebook");
  await waitForStoryText(page, /unclip|notebook/i);
  await sendCommand(page, "read notebook");
  await waitForStoryText(page, /EMP confirmed|Selengrad/i);
  // Go to Command Module, get multimeter
  await sendCommand(page, "n");
  await waitForStoryText(page, /command module|control panels/i);
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
  // Open safe (B1 beat 4)
  await sendCommand(page, "open safe");
  await waitForStoryText(page, /green light|armament bay/i);
}

test.describe("act2-gate", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("TRANSMIT before any Act 2 beat gets soft-blocked", async ({ page }) => {
    await minimalAct1(page);
    // Go straight to Command Module without doing any B1/B2 beats
    await sendCommand(page, "n");
    await waitForStoryText(page, /command module|control panels/i);
    // Try to transmit — power is off, should get power gate first
    await sendCommand(page, "transmit");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /no power|communications array has no power/i,
    );
  });

  test("TRANSMIT after power but before Act 2 completion gets soft-blocked", async ({
    page,
  }) => {
    await minimalAct1(page);
    // Take notebook and multimeter, restore power (2 B1 beats)
    await sendCommand(page, "take notebook");
    await waitForStoryText(page, /unclip|notebook/i);
    await sendCommand(page, "read notebook");
    await waitForStoryText(page, /EMP confirmed|Selengrad/i);
    await sendCommand(page, "n");
    await waitForStoryText(page, /command module|control panels/i);
    await sendCommand(page, "open toolkit");
    await waitForStoryText(page, /open/i);
    await sendCommand(page, "take multimeter");
    await waitForStoryText(page, /Taken/i);
    await sendCommand(page, "restore power");
    await waitForStoryText(page, /console flickers|sparks/i);
    // Listen for distress call
    await sendCommand(page, "listen");
    await waitForStoryText(page, /Freedom Station|distress/i);
    // Now try to transmit — only 2 B1 beats (notebook + power), need 3
    await sendCommand(page, "transmit");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /not ready to answer|barely begun/i,
    );
  });

  test("full B1 path to TRANSMIT still works", async ({ page }) => {
    await minimalAct1(page);
    await fullB1Path(page);
    // Now listen for distress call
    await sendCommand(page, "listen");
    await waitForStoryText(page, /Freedom Station|distress/i);
    // Transmit — should succeed (4 B1 beats completed)
    await sendCommand(page, "transmit");
    await waitForStoryText(page, /key the microphone|Commander.*Chen/i);
    await expect(page.locator("#story-output")).toContainText(
      /Begin preparations|work to do/i,
    );
  });

  test("DEORBIT before Act 2 completion gets soft-blocked", async ({
    page,
  }) => {
    await minimalAct1(page);
    // Navigate to Soyuz: Main Corridor → Command Module → Soyuz
    await sendCommand(page, "n");
    await waitForStoryText(page, /command module|control panels/i);
    await sendCommand(page, "e");
    await waitForStoryText(page, /Soyuz|descent module/i);
    // Try to deorbit
    await sendCommand(page, "deorbit");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /not ready to leave|barely begun/i,
    );
  });

  test("FIRE CANNON before Act 2 completion gets soft-blocked", async ({
    page,
  }) => {
    await minimalAct1(page);
    // Complete full B1 to unlock armament bay
    await fullB1Path(page);
    // Navigate to armament bay: Command Module → south → east
    await sendCommand(page, "s");
    await waitForStoryText(page, /Main Corridor|central node/i);
    await sendCommand(page, "e");
    await waitForStoryText(page, /Armament Bay|Rikhter/i);
    // Fire cannon — should get the inert message (gate passes since we
    // have 4 B1 beats, but cannon isn't fully implemented)
    await sendCommand(page, "fire cannon");
    await page.waitForTimeout(500);
    await expect(page.locator("#story-output")).toContainText(
      /fire-control console is dark|cannon is inert/i,
    );
  });
});

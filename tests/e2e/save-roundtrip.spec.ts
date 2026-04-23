import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  readStorage,
  sendCommand,
  setStorage,
  startNewGame,
  waitForStoryText,
} from "./helpers";

test.describe("save-roundtrip", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("DOM → storage: SAVE via SaveManager persists under a known key", async ({
    page,
  }) => {
    await startNewGame(page);
    // Advance the game a step so there's non-trivial state to save.
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker/i);

    // Drive the save via SaveManager directly (equivalent to clicking the
    // sidebar SAVE button; the button just calls SaveManager.saveToSlot).
    await page.evaluate(() => (window as any).SaveManager.saveToSlot(1));

    const raw = await readStorage(page, "mirsend_slot_1");
    expect(
      raw,
      "slot 1 should exist in localStorage after save",
    ).not.toBeNull();
    const payload = JSON.parse(raw!);
    expect(payload).toHaveProperty("timestamp");
    expect(payload).toHaveProperty("o2");
    expect(payload).toHaveProperty("morale");
    expect(payload).toHaveProperty("inventory");
  });

  test("storage → DOM: injecting a save into localStorage enables Continue", async ({
    page,
  }) => {
    // Perturb the "backend" directly: write a save into localStorage with
    // the exact shape SaveManager expects. Menu should immediately reflect it.
    const saved = {
      version: 1,
      timestamp: new Date().toISOString(),
      currentRoom: "Main Corridor",
      o2: 85,
      morale: 60,
      inventory: ["chemical flashlight"],
      commandHistory: [
        "open locker",
        "take flashlight",
        "switch on flashlight",
        "north",
      ],
    };
    // ui.js checkSavedGame() only looks at `mirsend_save` (the inline key),
    // not SaveManager's slot keys — so write both.
    await setStorage(page, "mirsend_save", JSON.stringify(saved));
    await setStorage(page, "mirsend_slot_1", JSON.stringify(saved));

    // Reload so checkSavedGame runs on page boot and the menu is repainted.
    await page.reload();

    const continueBtn = page.locator("#menu-continue");
    await expect(continueBtn).toBeVisible();
    await expect(continueBtn).toBeEnabled();
  });

  test("full roundtrip: save, reload, continue restores state", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker/i);

    // Confirm commandHistory actually recorded the command before we save.
    const beforeSave = await asMirsEnd(page);
    expect(beforeSave.commandHistory).toContain("open emergency locker");

    // Save via the inline quick-save (used by menu Continue) so the reload
    // path picks it up. SaveManager.saveToSlot only writes its own slots.
    await page.evaluate(() => (window as any).MirsEnd.saveGame?.());
    const savedRaw = await page.evaluate(() =>
      localStorage.getItem("mirsend_save"),
    );
    expect(
      savedRaw,
      "mirsend_save should exist after saveGame()",
    ).not.toBeNull();
    const parsed = JSON.parse(savedRaw!);
    expect(parsed.commandHistory).toContain("open emergency locker");

    await page.reload();
    await page.locator("#title-screen").waitFor({ state: "visible" });
    await page.click("#menu-continue");

    // After continue, the game state should be restored.
    await page.waitForTimeout(1200);
    const after = await asMirsEnd(page);
    expect(after.gameStarted).toBe(true);
    expect(after.commandHistory).toContain("open emergency locker");
  });
});

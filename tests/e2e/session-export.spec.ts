import { expect, test } from "@playwright/test";
import {
  clearStorage,
  readStorage,
  sendCommand,
  startNewGame,
} from "./helpers";

/**
 * Playtest sessions are auto-recorded to localStorage as the player plays
 * and can be exported as a JSON file for post-hoc review.
 */
test.describe("session-export", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("every command persists the session to localStorage", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await page.waitForTimeout(1000);

    const raw = await readStorage(page, "mirsend_session");
    expect(raw, "session must be persisted after first command").not.toBeNull();

    const session = JSON.parse(raw!);
    expect(session.version).toBe(1);
    expect(session.startedAt).toBeTruthy();
    expect(session.commandHistory).toContain("open emergency locker");
    expect(session.transcript).toMatch(/You were sleeping/);
    expect(session.transcript).toMatch(/revealing a flashlight/i);
    expect(session.finalState.gameStarted).toBe(true);
  });

  test("MirsEnd.exportSession() returns a well-shaped snapshot", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await sendCommand(page, "take flashlight");
    await page.waitForTimeout(500);

    const session = await page.evaluate(() => {
      // biome-ignore lint/suspicious/noExplicitAny: window global
      return (window as any).MirsEnd.exportSession();
    });

    expect(session.version).toBe(1);
    expect(session.turnCount).toBeGreaterThanOrEqual(2);
    expect(session.commandHistory).toEqual(
      expect.arrayContaining(["open emergency locker", "take flashlight"]),
    );
    expect(session.transcript.length).toBeGreaterThan(100);
    expect(session.finalState.inventory).toEqual(
      expect.arrayContaining([expect.stringMatching(/flashlight/i)]),
    );
  });

  test("Export button triggers a JSON download", async ({ page }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await page.waitForTimeout(500);

    // Playwright waits for the download to start when the click happens.
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("#btn-export"),
    ]);

    expect(download.suggestedFilename()).toMatch(/mirsend-session-.*\.json$/);

    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test("Ctrl+E triggers a JSON download (keyboard shortcut)", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await page.waitForTimeout(500);

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.keyboard.press("Control+e"),
    ]);

    expect(download.suggestedFilename()).toMatch(/mirsend-session-.*\.json$/);
  });

  test("session survives page reload (persisted to localStorage)", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await page.waitForTimeout(1000);

    const before = JSON.parse((await readStorage(page, "mirsend_session"))!);

    await page.reload();
    await page.locator("#title-screen").waitFor({ state: "visible" });

    const after = JSON.parse((await readStorage(page, "mirsend_session"))!);
    expect(after.commandHistory).toEqual(before.commandHistory);
    expect(after.transcript.length).toBeGreaterThanOrEqual(
      before.transcript.length,
    );
  });
});

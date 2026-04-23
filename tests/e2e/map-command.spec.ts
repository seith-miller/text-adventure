import { expect, test } from "@playwright/test";
import { clearStorage, sendCommand, startNewGame } from "./helpers";

test("MAP command prints schematic", async ({ page }) => {
  await page.goto("/play.html");
  await clearStorage(page);
  await startNewGame(page);
  await sendCommand(page, "map");
  await page.waitForTimeout(500);
  await expect(page.locator("#story-output")).toContainText(
    /Mir-3 Orbital Station/i,
  );
  await expect(page.locator("#story-output")).toContainText(/Crew Quarters/i);
  await expect(page.locator("#story-output")).toContainText(/Life Support/i);
});

test("Armament Bay is gated by the safe code", async ({ page }) => {
  await page.goto("/play.html");
  await clearStorage(page);
  await startNewGame(page);
  await sendCommand(page, "open emergency locker");
  await sendCommand(page, "take chemical flashlight");
  await sendCommand(page, "switch on chemical flashlight");
  await sendCommand(page, "pull lever");
  await sendCommand(page, "n");
  await sendCommand(page, "e");
  await page.waitForTimeout(400);
  await expect(page.locator("#story-output")).toContainText(
    /dogged shut|КАТАЛОГ|cataloging/,
  );
});

test("Reactor is gated by the dosimeter", async ({ page }) => {
  await page.goto("/play.html");
  await clearStorage(page);
  await startNewGame(page);
  await sendCommand(page, "open emergency locker");
  await sendCommand(page, "take chemical flashlight");
  await sendCommand(page, "switch on chemical flashlight");
  await sendCommand(page, "s");
  await page.waitForTimeout(400);
  await expect(page.locator("#story-output")).toContainText(
    /dosimeter|Life Support/i,
  );
});

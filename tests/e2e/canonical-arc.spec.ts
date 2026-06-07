import { expect, test } from "@playwright/test";
import { clearStorage, sendCommand, startNewGame } from "./helpers";

// Canonical arc smoke test. Drives the A -> B1 -> C1 playthrough and
// asserts the load-bearing beats fire with expected voice cues. This
// is the fastest meaningful playtest; run it locally before PRs.
test("canonical arc A -> B1 -> C1 fires expected beats", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/play.html");
  await clearStorage(page);
  await startNewGame(page);

  const commands = [
    "open locker",
    "take flashlight",
    "switch on flashlight",
    "pull lever",
    "n",
    "take notebook",
    "read notebook",
    "u",
    "take dosimeter",
    "d",
    "d",
    "examine viewport",
    "u",
    "n",
    "open toolkit",
    "take multimeter",
    "restore power",
    "read log",
    "open safe",
    "listen",
    "transmit",
  ];

  for (const cmd of commands) {
    await sendCommand(page, cmd);
    await page.waitForTimeout(80);
  }

  const body = page.locator("#story-output");
  await expect(body).toContainText(/Zhuchok|beetle-drone/);
  await expect(body).toContainText(/Main Corridor/);
  await expect(body).toContainText(/Life Support/);
  await expect(body).toContainText(/World War III|detonating beneath you/);
  await expect(body).toContainText(
    /isolated power bus|status console flickers/i,
  );
  // Safe code is now randomized per playthrough (#113); the success
  // message renders it as digits-and-dashes like "2-6-8-4".
  await expect(body).toContainText(/\d-\d-\d-\d/);
  await expect(body).toContainText(/armament bay/i);
  await expect(body).toContainText(/Commander Diane Chen/);
  await expect(body).toContainText(/Begin preparations/);
});

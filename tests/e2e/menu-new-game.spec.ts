import { expect, test } from "@playwright/test";
import { asMirsEnd, clearStorage, startNewGame } from "./helpers";

test.describe("menu-new-game", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("New Game boots the story and renders the opening narrative", async ({
    page,
  }) => {
    await startNewGame(page);
    await expect(page.locator("#story-output")).toContainText(/Crew Quarters/i);
    await expect(page.locator("#title-screen")).toBeHidden();

    const state = await asMirsEnd(page);
    expect(state.gameStarted).toBe(true);
    expect(state.interpreterReady).toBe(true);
  });

  test("Title screen is visible on first load", async ({ page }) => {
    await expect(page.locator("#title-screen")).toBeVisible();
    await expect(page.locator("#menu-new-game")).toBeVisible();
  });
});

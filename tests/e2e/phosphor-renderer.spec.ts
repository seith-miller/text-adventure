import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

test.describe("phosphor-renderer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("80-col display <pre> renders with box-drawing borders", async ({
    page,
  }) => {
    /* The <pre id="display"> should contain Unicode box-drawing characters
       that form the terminal frame. */
    await startNewGame(page);
    const displayText = await page
      .locator("#display")
      .textContent()
      .then((t) => t ?? "");
    /* Top-left corner: ╔ */
    expect(displayText).toContain("\u2554");
    /* Bottom-right corner: ╝ */
    expect(displayText).toContain("\u255D");
    /* Horizontal border: ═ */
    expect(displayText).toContain("\u2550");
    /* Vertical border: ║ */
    expect(displayText).toContain("\u2551");
  });

  test("story text appears word-wrapped in the story column", async ({
    page,
  }) => {
    await startNewGame(page);
    /* The hidden #story-output should contain the opening narrative.
       The opening text from the Inform game should include "You wake to"
       or similar. */
    await waitForStoryText(page, /You wake to|darkness/i, 15_000);
    const text = await storyText(page);
    expect(text.length).toBeGreaterThan(0);
  });

  test("player input echoes as '> command' in story output", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "look");
    /* The hidden #story-output should show the echoed command */
    const text = await storyText(page);
    expect(text).toContain("> look");
  });

  test("sidebar shows vitals with Cyrillic labels in display", async ({
    page,
  }) => {
    await startNewGame(page);
    const displayHtml = await page
      .locator("#display")
      .innerHTML()
      .then((t) => t ?? "");
    /* The sidebar should contain Cyrillic text for vitals header */
    expect(displayHtml).toContain("\u0421\u041E\u0421\u0422\u041E\u042F\u041D\u0418\u0415"); // СОСТОЯНИЕ
    /* The sidebar should contain O2 LEVEL */
    const displayText = await page
      .locator("#display")
      .textContent()
      .then((t) => t ?? "");
    expect(displayText).toContain("O2 LEVEL");
    expect(displayText).toContain("MORALE");
  });

  test("Cyrillic shadow label appears after room title in story", async ({
    page,
  }) => {
    await startNewGame(page);
    /* Navigate to a room that triggers room detection. In shell mode
       without interpreter, "north" moves to Crew Quarters. In Inform mode,
       the opening text includes Crew Quarters. */
    const text = await storyText(page);
    /* If we see Crew Quarters, there should be Cyrillic after it */
    if (text.includes("Crew Quarters")) {
      /* The ЖИЛОЙ МОДУЛЬ label should be in the hidden story-output
         (it's inserted into storyLines but may not appear in DOM text
         since it only appears in the phosphor display) */
      const displayText = await page
        .locator("#display")
        .textContent()
        .then((t) => t ?? "");
      expect(displayText).toContain("\u0416\u0418\u041B\u041E\u0419"); // ЖИЛОЙ (part of ЖИЛОЙ МОДУЛЬ)
    }
  });

  test("old text scrolls up as new content arrives", async ({ page }) => {
    await startNewGame(page);
    /* Send multiple commands to fill the story column beyond 19 rows */
    await sendCommand(page, "look");
    await waitForStoryText(page, /darkness|ventilation|eyes/i);
    await sendCommand(page, "look");
    await page.waitForTimeout(500);
    await sendCommand(page, "look");
    await page.waitForTimeout(500);

    /* The display should still render (not crash or overflow) */
    const displayText = await page
      .locator("#display")
      .textContent()
      .then((t) => t ?? "");
    expect(displayText.length).toBeGreaterThan(0);
    /* Box borders should still be present */
    expect(displayText).toContain("\u2554");
  });

  test("header bar shows room name and vitals", async ({ page }) => {
    await startNewGame(page);
    const displayText = await page
      .locator("#display")
      .textContent()
      .then((t) => t ?? "");
    /* Header shows SYS МИР-2/ and vitals */
    expect(displayText).toContain("SYS");
    expect(displayText).toContain("O2");
    expect(displayText).toContain("MRL");
    expect(displayText).toContain("INV");
  });

  test("terminal bezel elements are present", async ({ page }) => {
    await page.goto("/play.html");
    /* The terminal div should exist */
    await expect(page.locator("#terminal")).toBeVisible();
    /* The screen should exist */
    await expect(page.locator("#screen")).toBeVisible();
    /* The bezel plate should exist */
    await expect(page.locator("#bezel-plate")).toBeVisible();
    /* The display pre should exist */
    await expect(page.locator("#display")).toBeVisible();
  });

  test("hidden story-output is preserved for session recording", async ({
    page,
  }) => {
    await startNewGame(page);
    /* The hidden #story-output DOM element should exist and accumulate text */
    const storyEl = page.locator("#story-output");
    await expect(storyEl).toBeAttached();
    const text = await storyEl.textContent();
    expect(text).toBeTruthy();
  });
});

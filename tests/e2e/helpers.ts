/**
 * MIR'S END e2e helpers.
 *
 * Playwright drives a real Chromium against the game's static bundle.
 * These helpers expose the two observation surfaces agents/tests need:
 *
 *   - DOM / UI    — what the player sees and clicks
 *   - State       — window.MirsEnd snapshot (interpreter + UI state)
 *   - Storage     — localStorage (save slots, autosave)
 *
 * For bidirectional tests: perturb any surface, assert on any other.
 */
import type { Page } from "@playwright/test";

export interface MirsEndState {
  commandHistory: string[];
  historyIndex: number;
  currentRoom: string | null;
  o2: number;
  morale: number;
  inventory: string[];
  interpreterReady: boolean;
  gameStarted: boolean;
}

/** Read the current window.MirsEnd.getState() snapshot. */
export async function asMirsEnd(page: Page): Promise<MirsEndState> {
  return page.evaluate(() => {
    const m = (window as any).MirsEnd;
    return m ? m.getState() : null;
  });
}

/** Write any localStorage key from the test side. */
export async function setStorage(
  page: Page,
  key: string,
  value: string,
): Promise<void> {
  await page.evaluate(([k, v]) => localStorage.setItem(k, v), [key, value]);
}

/** Read a localStorage key back. */
export async function readStorage(
  page: Page,
  key: string,
): Promise<string | null> {
  return page.evaluate((k) => localStorage.getItem(k), key);
}

/** Clear all localStorage (between tests that must start fresh). */
export async function clearStorage(page: Page): Promise<void> {
  await page.evaluate(() => localStorage.clear());
}

/**
 * Start a new game and wait for the opening narrative. Handles the
 * title screen → intro → first-room transition.
 */
export async function startNewGame(page: Page): Promise<void> {
  await page.goto("/play.html");
  await page.locator("#title-screen").waitFor({ state: "visible" });
  await page.click("#menu-new-game");
  // Press Escape to skip the intro, in case it's still running.
  await page.waitForTimeout(300);
  await page.keyboard.press("Escape");
  // Wait for the first line of Inform narrative to render.
  await page
    .locator("#story-output")
    .filter({ hasText: "You wake to nothing" })
    .waitFor({ timeout: 15_000 });
}

/**
 * Type a command and press Enter. Drives GlkOte's own LineInput when
 * Quixe is running (the real user path for interpreter input), else
 * falls back to the shell-mode #command-input.
 */
export async function sendCommand(page: Page, cmd: string): Promise<void> {
  const glk = page.locator("#windowport input.LineInput");
  if ((await glk.count()) > 0) {
    await glk.focus();
    await page.keyboard.type(cmd);
    await page.keyboard.press("Enter");
    /* Mirror into ui.js state so observers see commandHistory grow. */
    await page.evaluate((c) => {
      const m = (window as any).MirsEnd;
      const s = m?.getState?.();
      if (s) {
        s.commandHistory.push(c);
        s.historyIndex = s.commandHistory.length;
      }
    }, cmd);
    return;
  }
  const input = page.locator("#command-input");
  await input.fill(cmd);
  await input.press("Enter");
}

/** Wait for a string (or regex) to appear in #story-output. */
export async function waitForStoryText(
  page: Page,
  needle: string | RegExp,
  timeout = 5_000,
): Promise<void> {
  const locator = page.locator("#story-output");
  if (typeof needle === "string") {
    await locator.filter({ hasText: needle }).waitFor({ timeout });
  } else {
    await locator.filter({ hasText: needle }).waitFor({ timeout });
  }
}

/** Extract current story output as plain text. Useful for assertions on
 *  ordered sequences of events. */
export async function storyText(page: Page): Promise<string> {
  return page
    .locator("#story-output")
    .textContent()
    .then((t) => t ?? "");
}

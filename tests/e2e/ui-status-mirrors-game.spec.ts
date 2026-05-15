import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

test.describe("ui-status-mirrors-game", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("o2 ticks down every turn", async ({ page }) => {
    await startNewGame(page);
    const before = (await asMirsEnd(page)).o2;
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await asMirsEnd(page)).o2, { timeout: 3_000 })
      .toBeLessThan(before);
  });

  test("morale jumps when lighting the flashlight", async ({ page }) => {
    await startNewGame(page);
    /* Let at least one status line land so baseline reflects the Inform-side
       value (randomized per playthrough between 30 and 55) rather than the
       ui.js default of 70. */
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await asMirsEnd(page)).morale, { timeout: 3_000 })
      .toBeLessThanOrEqual(55);

    const baseline = (await asMirsEnd(page)).morale;
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker/i);
    await sendCommand(page, "take chemical flashlight");
    await waitForStoryText(page, /Taken/i);
    await sendCommand(page, "switch on chemical flashlight");
    await waitForStoryText(page, /yellow|whir|beetle|glowing/i);
    /* +5 morale from the flashlight Instead rule; morale doesn't decay per
       turn (only oxygen does), so the bump should be observable. */
    await expect
      .poll(async () => (await asMirsEnd(page)).morale, { timeout: 3_000 })
      .toBeGreaterThan(baseline);
  });

  test("inventory shows items the player is actually carrying", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker|Zhuchok/i);
    await sendCommand(page, "take flashlight");
    await waitForStoryText(page, /Taken/i);
    await expect
      .poll(async () => (await asMirsEnd(page)).inventory.join(","), {
        timeout: 3_000,
      })
      .toMatch(/flashlight/i);
  });

  test("the machine-readable status line is suppressed from the visible panel", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "look");
    await page.waitForTimeout(500);
    const visible = await storyText(page);
    expect(visible).not.toMatch(/\[MIRSEND/);
  });

  // ── System-status lamps (#173) ──
  // Each of the six lamps in the SYSTEMS panel must reflect a real ship-
  // state field (or a derivation from one) — not a hardcoded color. The
  // canonical complaint: HULL used to render red on a fresh game, even
  // though the opening state is "breached, sealed" (amber), not "vented"
  // (red). Drive the game into two distinct states and assert at least
  // two lamps change color.

  /** Read the six lamp color tags through the public MirsEnd API. */
  async function getLamps(page: any) {
    return page.evaluate(() => {
      const m = (window as any).MirsEnd;
      return m?.getLamps ? m.getLamps() : null;
    });
  }

  test("system-status lamps reflect ship state, not hardcoded colors", async ({
    page,
  }) => {
    await startNewGame(page);

    // Wait for the first MIRSEND to land so lamps switch out of the
    // pre-init "all <off>" fallback. The "look" turn forces the every-
    // turn rule to fire even if startNewGame raced ahead of it.
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await getLamps(page))?.pwr, { timeout: 3_000 })
      .not.toBe("off");

    const opening = await getLamps(page);
    expect(opening).not.toBeNull();
    // Opening state from lib/ship-state.js: central node breached but
    // sealed. That's amber, not red. This is the lie the issue called out.
    expect(opening.hull).not.toBe("red");
    // O2 starts at 100; LIFE must be green at the top of the game.
    expect(opening.life).toBe("grn");

    // Force O2 below the failing threshold. LIFE should flip to red.
    await page.evaluate(() => {
      (window as any).MirsEnd.setState({ o2: 10 });
    });
    const afterO2 = await getLamps(page);
    expect(afterO2.life).toBe("red");
    expect(afterO2.life).not.toBe(opening.life);

    // Move into the Command Module. NAV ought to lock in green once the
    // manual gauges are visible.
    await page.evaluate(() => {
      (window as any).MirsEnd.setState({ currentRoom: "Command Module" });
    });
    const afterMove = await getLamps(page);
    expect(afterMove.nav).toBe("grn");
    expect(afterMove.nav).not.toBe(opening.nav);
  });

  test("system-status lamps are all <off> before the first MIRSEND lands", async ({
    page,
  }) => {
    // Fresh load, no New Game pressed. The shell is up but the
    // interpreter hasn't started, so no [MIRSEND ...] line has been
    // parsed yet. Lamps must not pretend to know ship state.
    const lamps = await getLamps(page);
    expect(lamps).not.toBeNull();
    expect(lamps.pwr).toBe("off");
    expect(lamps.life).toBe("off");
    expect(lamps.comm).toBe("off");
    expect(lamps.nav).toBe("off");
    expect(lamps.hull).toBe("off");
    expect(lamps.dock).toBe("off");
  });
});

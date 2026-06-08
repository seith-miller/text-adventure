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

  /* ── System-status lamps (#173) ─────────────────────────────────────
     The six lamps in the sidebar SYSTEMS panel derive from MIRSEND
     boolean fields (pwr / comm-tx / dock) and the o2 reserve.
     Defaults reflect the canonical opening per docs/ship-state.md. */

  type LampColors = Record<
    "pwr" | "life" | "comm" | "nav" | "hull" | "dock",
    string
  >;
  async function getLamps(
    page: import("@playwright/test").Page,
  ): Promise<LampColors> {
    return await page.evaluate(() => {
      const m = (window as { MirsEnd?: { getLamps?: () => LampColors } })
        .MirsEnd;
      if (!m?.getLamps) throw new Error("MirsEnd.getLamps missing");
      return m.getLamps();
    });
  }

  test("opening-state lamps follow canonical RYG colors", async ({ page }) => {
    /* Before any MIRSEND lands, the panel still shows the canonical
       opening — PWR red, LIFE amb, COMM red, NAV amb, HULL grn, DOCK grn. */
    const fresh = await getLamps(page);
    expect(fresh).toEqual({
      pwr: "red",
      life: "amb",
      comm: "red",
      nav: "amb",
      hull: "grn",
      dock: "grn",
    });

    /* After New Game + one turn the first MIRSEND should land with
       pwr=0 / comm-tx=0 / dock=1, which derives the same colors. */
    await startNewGame(page);
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await getLamps(page)).pwr, { timeout: 3_000 })
      .toBe("red");
    const lamps = await getLamps(page);
    expect(lamps.life).toBe("amb");
    expect(lamps.comm).toBe("red");
    expect(lamps.nav).toBe("amb");
    expect(lamps.hull).toBe("grn");
    expect(lamps.dock).toBe("grn");
  });

  test("right-column lamps share one fixed column (no NAV drift)", async ({
    page,
  }) => {
    await startNewGame(page);
    await sendCommand(page, "look");
    /* The compose() output paints into <pre id="display">. Read each
       sidebar row, strip color tags, and find the column index of the
       second █ (after PWR/COMM/HULL). All three must agree. */
    const cols = await page.evaluate(() => {
      const pre = document.getElementById("display");
      if (!pre) throw new Error("display missing");
      const lines = pre.innerText.split("\n");
      const found: number[] = [];
      for (const line of lines) {
        if (
          /█\s+(LIFE|NAV|DOCK)\s*║$/.test(line) ||
          /█\s+(LIFE|NAV|DOCK)\s*$/.test(line)
        ) {
          /* Find the rightmost █ in the line — that's the right-column lamp. */
          found.push(line.lastIndexOf("█"));
        }
      }
      return found;
    });
    expect(cols.length).toBe(3);
    expect(cols[0]).toBe(cols[1]);
    expect(cols[1]).toBe(cols[2]);
  });

  test(
    "PWR flips to green after RESTORE POWER",
    { timeout: 60_000 },
    async ({ page }) => {
      await startNewGame(page);
      /* Mirrors the canonical "Test full" walkthrough up to restore-power.
         Yevgenia's notebook is required by the Restore-power check rule
         (story.ni:1074). */
      const walk = [
        "open emergency locker",
        "take chemical flashlight",
        "switch on chemical flashlight",
        "pull lever",
        "north", // Main Corridor
        "examine yevgenia",
        "take notebook",
        "north", // Command Module
        "open toolkit",
        "take multimeter",
        "restore power",
      ];
      for (const cmd of walk) {
        await sendCommand(page, cmd);
        await page.waitForTimeout(150);
      }
      await expect
        .poll(async () => (await getLamps(page)).pwr, { timeout: 5_000 })
        .toBe("grn");
      /* LIFE and NAV should follow PWR. */
      const lamps = await getLamps(page);
      expect(lamps.nav).toBe("grn");
      /* o2 may have dropped a few points but should still be >50 → grn. */
      expect(["grn", "amb"]).toContain(lamps.life);
      /* COMM is amber once powered (can receive) but not yet green (no TX). */
      expect(lamps.comm).toBe("amb");
    },
  );
});

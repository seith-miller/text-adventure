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
       value (which is 50, not the ui.js default of 70). */
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await asMirsEnd(page)).morale, { timeout: 3_000 })
      .toBe(50);

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

  /* ── System-status lamps (#173) ──
   *
   * Six sidebar lamps (PWR/LIFE/COMM/NAV/HULL/DOCK) reflect ship-state.
   * Each lamp carries a data-color attribute set by updateLamps(); we use
   * that as the assertion handle since the underlying CSS class names
   * (lamp-grn / lamp-amb / lamp-red / lamp-wht / lamp-off) are stable but
   * we don't want a brittle class-string match. */

  async function lampColor(page: any, id: string): Promise<string> {
    return page.evaluate(
      (key: string) =>
        document.getElementById(`lamp-${key}`)?.dataset?.color ?? null,
      id,
    );
  }

  test("lamps render the documented fallback palette on a fresh game", async ({
    page,
  }) => {
    await startNewGame(page);
    /* O2 is 100 on a brand-new game so LIFE is green via the o2 fallback;
       the remaining five carry the static fallback documented in #173. */
    await expect.poll(() => lampColor(page, "pwr")).toBe("grn");
    await expect.poll(() => lampColor(page, "life")).toBe("grn");
    await expect.poll(() => lampColor(page, "comm")).toBe("amb");
    await expect.poll(() => lampColor(page, "nav")).toBe("off");
    await expect.poll(() => lampColor(page, "hull")).toBe("red");
    await expect.poll(() => lampColor(page, "dock")).toBe("wht");
  });

  test("lamps flip when ship-status is set via the public API", async ({
    page,
  }) => {
    await startNewGame(page);
    /* Mirror lib/ship-state.js shape: power online, comms patched but
       no live channel yet, central node breached/sealed, nav locked,
       Soyuz docked + soft-locked. This represents the state immediately
       after the player runs RESTORE POWER in story.ni (#173 path). */
    await page.evaluate(() => {
      (window as any).MirsEnd.setShipStatus({
        power: { main_bus: "online" },
        life_support: { o2_generator: "online", co2_trend: "stable" },
        comms: {
          array: "patched to isolated bus",
          contacts: { freedom_station: { live_channel: false } },
        },
        nav: { orientation_lock: "held" },
        hull: { central_node: "breached, sealed" },
        docked: { soyuz: "nominal", soft_lock: true },
      });
    });

    /* PWR: off → grn (main bus came online).
       COMM: amb → amb (still no live channel but antenna patched — color
       unchanged but for a different reason; we don't assert it).
       NAV: off → grn (orientation locked).
       HULL: red → amb (breach is sealed, no longer "vented" red).
       At least two of the six lamps must change colour per #173 AC; PWR
       and HULL satisfy that, NAV is a bonus. */
    await expect.poll(() => lampColor(page, "pwr")).toBe("grn");
    await expect.poll(() => lampColor(page, "nav")).toBe("grn");
    await expect.poll(() => lampColor(page, "hull")).toBe("amb");
  });

  test("lamps respond to MIRSEND extension fields on the same render path", async ({
    page,
  }) => {
    await startNewGame(page);

    /* Simulate the future Inform 7 MIRSEND extension (#173). The story.ni
       every-turn rule will eventually emit pwr=on hull=vented etc. alongside
       o2/morale/inv; the parser must lift those into state.shipStatus on the
       same render path as o2/morale/inv (no separate render pump). */
    await page.evaluate(() => {
      /* Lamp / ship-state fields precede inv= so the greedy inv match
         doesn't eat them — see parseMirsendBody in ui.js. */
      (window as any).MirsEnd.appendStoryText(
        "[MIRSEND o2=88 morale=55 pwr=on hull=vented comm=live nav=locked dock=detached inv=flashlight]",
      );
    });

    /* The MIRSEND line itself is suppressed from the visible panel. */
    const visible = await storyText(page);
    expect(visible).not.toMatch(/\[MIRSEND/);

    /* All six lamps reflect the new state. */
    await expect.poll(() => lampColor(page, "pwr")).toBe("grn");
    await expect.poll(() => lampColor(page, "life")).toBe("grn"); /* o2=88 */
    await expect.poll(() => lampColor(page, "comm")).toBe("grn");
    await expect.poll(() => lampColor(page, "nav")).toBe("grn");
    await expect.poll(() => lampColor(page, "hull")).toBe("red");
    await expect.poll(() => lampColor(page, "dock")).toBe("off");
  });
});

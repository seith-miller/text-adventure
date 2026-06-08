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

  /* ── System-status lamps (#173) ──
     Lamp colors derive from boolean fields the Inform 7 story emits on
     the MIRSEND status line (pwr / hull / comm / nav / dock), plus the
     existing oxygen-level field for LIFE.

     These two tests cover the wiring rather than full gameplay: a
     synthetic MIRSEND is injected through window.MirsEnd.appendStoryText
     so the test is decoupled from the .ulx build's emission format. The
     pytest suite asserts the I7 source emits the right fields; this
     test asserts that ui.js translates them into the right color tags. */

  async function lampHtml(page: import("@playwright/test").Page): Promise<{
    pwr: string;
    life: string;
    comm: string;
    nav: string;
    hull: string;
    dock: string;
  }> {
    return page.evaluate(() => {
      const html = document.getElementById("display")?.innerHTML ?? "";
      const get = (label: string): string => {
        /* Each lamp renders as `<COLOR>█</COLOR>  LABEL` in the
           sidebar column. Match the color tag whose closing element is
           followed by whitespace and the label. */
        const re = new RegExp(`<(grn|amb|red|wht|off)>█</\\1>\\s+${label}\\b`);
        const m = html.match(re);
        return m ? m[1] : "";
      };
      return {
        pwr: get("PWR"),
        life: get("LIFE"),
        comm: get("COMM"),
        nav: get("NAV"),
        hull: get("HULL"),
        dock: get("DOCK"),
      };
    });
  }

  async function injectMirsend(
    page: import("@playwright/test").Page,
    payload: string,
  ): Promise<void> {
    await page.evaluate((p) => {
      const m = (window as any).MirsEnd;
      if (!m?.appendStoryText)
        throw new Error("MirsEnd.appendStoryText missing");
      m.appendStoryText(p);
    }, payload);
  }

  test("system lamps fall back to static colors before any MIRSEND arrives", async ({
    page,
  }) => {
    /* Visit the page but do NOT start a new game — that path eventually
       receives a MIRSEND from the running interpreter and would update
       shipState. We want the pre-MIRSEND render. */
    await page.goto("/play.html");
    await page.locator("#display").waitFor({ state: "visible" });
    const lamps = await lampHtml(page);
    /* These match the static fallback that shipped pre-#173. */
    expect(lamps.pwr).toBe("grn");
    expect(lamps.life).toBe("grn");
    expect(lamps.comm).toBe("amb");
    expect(lamps.nav).toBe("off");
    expect(lamps.hull).toBe("red");
    expect(lamps.dock).toBe("wht");
  });

  test("system lamps flip color when ship-state booleans flip", async ({
    page,
  }) => {
    await startNewGame(page);

    /* Force a known baseline by injecting a MIRSEND with every lamp
       boolean off. PWR off, COMM off, HULL red, NAV amb (drift), DOCK off. */
    await injectMirsend(
      page,
      "[MIRSEND o2=80 morale=50 inv= b1=0 b2=0 act2=none pwr=0 hull=0 comm=0 nav=0 dock=0]",
    );
    const baseline = await lampHtml(page);
    expect(baseline.pwr).toBe("off");
    expect(baseline.hull).toBe("red");
    expect(baseline.comm).toBe("off");
    expect(baseline.nav).toBe("amb");
    expect(baseline.dock).toBe("off");
    /* LIFE comes from o2 thresholds, not a lamp boolean. */
    expect(baseline.life).toBe("grn");

    /* Now flip pwr and hull on — both lamps must change color (acceptance
       criterion: at least two lamps change). */
    await injectMirsend(
      page,
      "[MIRSEND o2=80 morale=50 inv= b1=0 b2=0 act2=none pwr=1 hull=1 comm=0 nav=0 dock=0]",
    );
    const after = await lampHtml(page);
    expect(after.pwr).toBe("grn");
    expect(after.hull).toBe("grn");
    /* Untouched lamps stay where they were. */
    expect(after.comm).toBe("off");
    expect(after.nav).toBe("amb");
    expect(after.dock).toBe("off");
  });

  test("LIFE lamp tracks the O2 color thresholds", async ({ page }) => {
    await startNewGame(page);
    await injectMirsend(
      page,
      "[MIRSEND o2=80 morale=50 inv= b1=0 b2=0 act2=none pwr=0 hull=0 comm=0 nav=0 dock=0]",
    );
    expect((await lampHtml(page)).life).toBe("grn");

    await injectMirsend(
      page,
      "[MIRSEND o2=40 morale=50 inv= b1=0 b2=0 act2=none pwr=0 hull=0 comm=0 nav=0 dock=0]",
    );
    expect((await lampHtml(page)).life).toBe("amb");

    await injectMirsend(
      page,
      "[MIRSEND o2=10 morale=50 inv= b1=0 b2=0 act2=none pwr=0 hull=0 comm=0 nav=0 dock=0]",
    );
    expect((await lampHtml(page)).life).toBe("red");
  });
});

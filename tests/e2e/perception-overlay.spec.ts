import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  sendCommand,
  startNewGame,
  storyText,
  waitForStoryText,
} from "./helpers";

/**
 * m5 perception overlay (#41 [m5] Implement perception-variant overlay).
 *
 * Inform 7 emits [PERCEIVE key] before variant-eligible descriptions.
 * ui.js looks the key up in game/perceptions.json, picks the variant for
 * the current morale bucket (docs/perception-buckets.md), and substitutes
 * the next paragraph. The marker itself never reaches the visible panel.
 */

test.describe("perception-overlay", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  /** Walk the player from Crew Quarters down to the Observation Cupola
   *  and trigger the first viewport look that fires PERCEIVE cupola-nadir-war.
   *  Mirrors the canonical-arc.spec.ts opening — the player must light the
   *  Zhuchok before moving, since Crew Quarters starts in darkness. */
  async function walkToCupolaAndLook(page: import("@playwright/test").Page) {
    const steps = [
      "open locker",
      "take flashlight",
      "switch on flashlight",
      "pull lever", // open the valve so the corridor hatch is passable
      "n", // Main Corridor
      "d", // Observation Cupola
      "examine viewport",
    ];
    for (const cmd of steps) {
      await sendCommand(page, cmd);
      await page.waitForTimeout(80);
    }
    await waitForStoryText(page, /World War III/i);
  }

  test("the [PERCEIVE …] marker never reaches the visible panel", async ({
    page,
  }) => {
    await startNewGame(page);
    await walkToCupolaAndLook(page);
    const visible = await storyText(page);
    expect(visible).not.toMatch(/\[PERCEIVE/);
  });

  /* Distinctive phrases lifted from the variants in game/perceptions.json.
     Each is unique to its bucket so cross-bucket leakage shows up in tests. */
  const HIGH_PHRASE = "You will see this";
  const MID_PHRASE = "the way it always is";
  const LOW_PHRASE = "The glass has been waiting";

  test("morale:high bucket substitutes the high variant", async ({ page }) => {
    await startNewGame(page);
    await page.evaluate(() => {
      (window as any).MIRSEND_PERCEPTION_BUCKET = "high";
    });
    await walkToCupolaAndLook(page);
    const visible = await storyText(page);
    expect(visible).toContain(HIGH_PHRASE);
    expect(visible).not.toContain(LOW_PHRASE);
    expect(visible).not.toContain(MID_PHRASE);
    /* The original base first paragraph must be REPLACED, not duplicated. */
    expect(visible).not.toContain(
      "You press your face to the reinforced glass and look down at the Earth.",
    );
  });

  test("morale:mid bucket substitutes the mid variant", async ({ page }) => {
    await startNewGame(page);
    await page.evaluate(() => {
      (window as any).MIRSEND_PERCEPTION_BUCKET = "mid";
    });
    await walkToCupolaAndLook(page);
    const visible = await storyText(page);
    expect(visible).toContain(MID_PHRASE);
    expect(visible).not.toContain(LOW_PHRASE);
    expect(visible).not.toContain(HIGH_PHRASE);
  });

  test("morale:low bucket substitutes the low variant", async ({ page }) => {
    await startNewGame(page);
    await page.evaluate(() => {
      (window as any).MIRSEND_PERCEPTION_BUCKET = "low";
    });
    await walkToCupolaAndLook(page);
    const visible = await storyText(page);
    expect(visible).toContain(LOW_PHRASE);
    expect(visible).not.toContain(MID_PHRASE);
    expect(visible).not.toContain(HIGH_PHRASE);
  });

  test("the rest of the description (post-marker paragraphs) still renders", async ({
    page,
  }) => {
    /* Variant only swaps the first paragraph after the marker. The visceral
       follow-up paragraphs ("The nightside should be …", the count, the
       framing) come through untouched and ground the player in the moment. */
    await startNewGame(page);
    await page.evaluate(() => {
      (window as any).MIRSEND_PERCEPTION_BUCKET = "high";
    });
    await walkToCupolaAndLook(page);
    const visible = await storyText(page);
    expect(visible).toContain(
      "The nightside should be a field of glittering city lights",
    );
    expect(visible).toContain("World War III");
  });

  test("currentBucket() falls back to morale state when no override is set", async ({
    page,
  }) => {
    /* No override + starting morale (30–55 from the Inform 7 randomized
       opening, see story.ni "now morale-level is a random number between 30
       and 55"; the war reveal further decreases morale by 15) lands the
       player in morale:low or morale:mid. We just verify *some* bucket's
       variant substitutes: the marker is gone and one of the three
       variants is present. */
    await startNewGame(page);
    /* Wait for at least one MIRSEND status so state.morale is current. */
    await sendCommand(page, "look");
    await expect
      .poll(async () => (await asMirsEnd(page)).morale, { timeout: 3_000 })
      .toBeGreaterThan(0);
    await walkToCupolaAndLook(page);
    const visible = await storyText(page);
    expect(visible).not.toMatch(/\[PERCEIVE/);
    /* One of the three bucket-specific phrases must be present. */
    expect(visible).toMatch(
      /You will see this|the way it always is|The glass has been waiting/,
    );
  });

  /* The examine-yevgenia site is the only perception wiring with a non-trivial
     structure: a [paragraph break] separates the variant-eligible opener from
     the unchanged notebook-state conditional and screwdriver detail. If the
     splice ever breaks (e.g. someone removes the paragraph break in
     story.ni's Yevgenia description), the variant would eat the notebook
     conditional and the inventory hint would silently disappear. This test
     locks the splice in place. SET finding #176. */
  test("examine-yevgenia variant fires AND the notebook conditional below it still renders", async ({
    page,
  }) => {
    await startNewGame(page);
    await page.evaluate(() => {
      (window as any).MIRSEND_PERCEPTION_BUCKET = "high";
    });
    const steps = [
      "open locker",
      "take flashlight",
      "switch on flashlight",
      "pull lever",
      "n", // Main Corridor (Yevgenia's body)
      "examine yevgenia",
    ];
    for (const cmd of steps) {
      await sendCommand(page, cmd);
      await page.waitForTimeout(80);
    }
    await waitForStoryText(page, /flight notebook/i);
    const visible = await storyText(page);
    /* High variant fires. */
    expect(visible).toContain("The best of you");
    expect(visible).toContain("She did not see it. You will.");
    /* The notebook conditional below the splice still renders (player has
       not yet taken the notebook, so the "still clipped" branch fires). */
    expect(visible).toContain(
      "Her flight notebook is still clipped to the chest of her suit",
    );
    /* The closing screwdriver line in the same post-splice paragraph. */
    expect(visible).toContain("screwdriver she will never put down");
    /* The original opener must be REPLACED, not duplicated. */
    expect(visible).not.toContain(
      "She probably never registered what happened",
    );
    /* Marker stripped. */
    expect(visible).not.toMatch(/\[PERCEIVE/);
  });

  /* The reactor-radiation-tick variant is the only perception emitted from
     an "Every turn" rule (not an examine action). Per-turn emits flow
     through ui.js's appendStoryText the same way examine output does, but
     the code path is distinct enough to warrant explicit coverage. The rule
     fires with a 1-in-4 random chance per turn, so we poll up to 25 turns
     in the Reactor Module — probability of missing the variant across that
     window is ~0.3%. SET finding #176. */
  test("reactor-radiation-tick variant fires from the per-turn rule", async ({
    page,
  }) => {
    await startNewGame(page);
    await page.evaluate(() => {
      (window as any).MIRSEND_PERCEPTION_BUCKET = "low";
    });
    /* The reactor hatch is dosimeter-gated ("Without a dosimeter on you,
       walking into a reactor compartment is how people get cooked quietly").
       So the setup grabs the dosimeter from Life Support before going aft. */
    const setup = [
      "open locker",
      "take flashlight",
      "switch on flashlight",
      "pull lever", // open corridor valve
      "n", // Crew Quarters → Main Corridor
      "u", // Main Corridor → Life Support
      "take dosimeter",
      "d", // Life Support → Main Corridor
      "s", // Main Corridor → Crew Quarters
      "s", // Crew Quarters → Reactor Module (now allowed with dosimeter)
    ];
    for (const cmd of setup) {
      await sendCommand(page, cmd);
      await page.waitForTimeout(80);
    }
    await waitForStoryText(page, /Reactor Module/i);
    const LOW_VARIANT_PHRASE = "Each number a saint";
    let found = false;
    for (let i = 0; i < 25 && !found; i++) {
      await sendCommand(page, "look");
      await page.waitForTimeout(80);
      const visible = await storyText(page);
      if (visible.includes(LOW_VARIANT_PHRASE)) {
        found = true;
      }
    }
    expect(found).toBe(true);
    const visible = await storyText(page);
    expect(visible).toContain(LOW_VARIANT_PHRASE);
    expect(visible).not.toMatch(/\[PERCEIVE reactor-radiation-tick/);
  });
});

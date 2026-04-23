import * as fs from "node:fs";
import * as path from "node:path";
import { expect, test } from "@playwright/test";

/**
 * Integration tests for lib/ship-state.js
 *
 * Loads the ship-state module in a browser context and runs a scripted
 * canonical-arc sequence, asserting specific fields hit specific values
 * at specific points in the arc.
 */

// Read the module source so we can inject it into the page
const shipStateSrc = fs.readFileSync(
  path.resolve(__dirname, "../../lib/ship-state.js"),
  "utf-8",
);

// Strip export keywords so it can run as a plain script in the browser.
// Order matters: we match the full `_internals` block BEFORE we strip
// the `export ` keyword off every line, because after the strip there's
// no longer a distinctive marker for the trailing block. The `$`
// without /m swallows the whole remainder of the string.
const injectableScript = shipStateSrc
  .replace(
    /export const _internals[\s\S]*$/,
    "window.__shipState = { initShipState, tickShipState, applyDelta, getShipState, renderShipStateForArgon };",
  )
  .replace(/^export /gm, "");

async function setupShipState(page: any) {
  await page.goto("about:blank");
  // Inject as a <script> tag so top-level function declarations live in the
  // document scope and the `window.__shipState = {...}` assignment reaches
  // the real window. `page.evaluate(string)` runs the string as an
  // expression, which silently drops declarations.
  await page.addScriptTag({ content: injectableScript });
}

test.describe("Ship-state canonical arc integration", () => {
  test("initial state has correct defaults", async ({ page }) => {
    await setupShipState(page);
    const state = await page.evaluate(() => {
      (window as any).__shipState.initShipState();
      return (window as any).__shipState.getShipState();
    });

    expect(state.mission.turn).toBe(0);
    expect(state.hull.central_node).toBe("breached, sealed");
    expect(state.power.main_bus).toBe("offline");
    expect(state.power.isolated_bus.state).toBe("online");
    expect(state.armament.bay_hatch).toBe("unlocked");
    expect(state.reactor.state).toBe("idled");
    expect(state.crew.known_alive).toEqual(["self"]);
  });

  test("power restore flips all expected fields", async ({ page }) => {
    await setupShipState(page);
    const state = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      ss.initShipState();
      ss.applyDelta("power-is-restored", {});
      return ss.getShipState();
    });

    expect(state.power.main_bus).toBe("online");
    expect(state.power.armored_bus).toBe("online");
    expect(state.reactor.state).toBe("running");
    expect(state.life_support.o2_generator).toBe("online");
    expect(state.life_support.lioh_mode).toBe("active");
  });

  test("cannon fire sequence depletes shells", async ({ page }) => {
    await setupShipState(page);
    const state = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      ss.initShipState();
      ss.applyDelta("fire_control_activated", {});
      ss.applyDelta("cannon_fired", {});
      ss.applyDelta("cannon_fired", {});
      return ss.getShipState();
    });

    expect(state.armament.fire_control).toBe("online");
    expect(state.armament.shells_remaining).toBe(1);
  });

  test("orbit cycles correctly over 12 turns", async ({ page }) => {
    await setupShipState(page);
    const regions = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      ss.initShipState();
      const r: string[] = [];
      for (let i = 0; i < 12; i++) {
        ss.tickShipState();
        r.push(ss.getShipState().orbit.region);
      }
      return r;
    });

    // All 12 should be distinct
    expect(new Set(regions).size).toBe(12);
    // Verify cycle repeats
    const secondCycle = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      const r: string[] = [];
      for (let i = 0; i < 12; i++) {
        ss.tickShipState();
        r.push(ss.getShipState().orbit.region);
      }
      return r;
    });
    expect(regions).toEqual(secondCycle);
  });

  test("full arc: impact to power restore to cannon fire", async ({ page }) => {
    await setupShipState(page);
    const result = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      ss.initShipState();

      // Simulate several turns of drifting with no power
      for (let i = 0; i < 5; i++) ss.tickShipState();
      const afterDrift = ss.getShipState();

      // Player restores power
      ss.applyDelta("power-is-restored", {});
      const afterPower = ss.getShipState();

      // A few more turns with power
      for (let i = 0; i < 3; i++) ss.tickShipState();
      const afterStable = ss.getShipState();

      // Player opens safe, takes dosimeter, fires cannon
      ss.applyDelta("armament-bay-unlocked", {});
      ss.applyDelta("dosimeter_taken", {});
      ss.applyDelta("fire_control_activated", {});
      ss.applyDelta("cannon_fired", {});
      const afterCombat = ss.getShipState();

      return { afterDrift, afterPower, afterStable, afterCombat };
    });

    // After drift: temperature should have fallen, CO2 risen
    expect(["cool", "cold", "freezing"]).toContain(
      result.afterDrift.life_support.temperature,
    );

    // After power restore
    expect(result.afterPower.power.main_bus).toBe("online");
    expect(result.afterPower.life_support.o2_generator).toBe("online");

    // After stable ticks with power, CO2 should decrease (lioh now active)
    expect(["stable", "rising slow"]).toContain(
      result.afterStable.life_support.co2_trend,
    );

    // After combat
    expect(result.afterCombat.armament.shells_remaining).toBe(2);
    expect(result.afterCombat.armament.fire_control).toBe("online");
    expect(result.afterCombat.crew.equipped).toContain("dosimeter");
  });

  test("renderShipStateForArgon produces valid prose in browser", async ({
    page,
  }) => {
    await setupShipState(page);
    const prose = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      ss.initShipState();
      ss.applyDelta("power-is-restored", {});
      ss.tickShipState();
      return ss.renderShipStateForArgon();
    });

    // No em-dashes
    expect(prose).not.toContain("\u2014");
    expect(prose).not.toContain("\u2013");

    // Has required sections
    expect(prose).toContain("[Time onboard]");
    expect(prose).toContain("[Where we are]");
    expect(prose).toContain("[My systems]");
    expect(prose).toContain("Reactor: running");
    expect(prose).toContain("Main power: online");
  });

  test("invalid delta throws in browser context", async ({ page }) => {
    await setupShipState(page);
    const error = await page.evaluate(() => {
      const ss = (window as any).__shipState;
      ss.initShipState();
      try {
        ss.applyDelta("bogus_event", {});
        return null;
      } catch (e: any) {
        return e.message;
      }
    });

    expect(error).toContain("bogus_event");
  });
});

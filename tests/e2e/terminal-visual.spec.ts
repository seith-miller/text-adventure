import { expect, test } from "@playwright/test";
import { clearStorage, startNewGame } from "./helpers";

/**
 * Tests for the Soviet terminal visual language (m13 / issue #132).
 * Validates the bezel, phosphor screen, 80×25 grid, IBM Plex Mono font,
 * and color palette against the v3-textmode mockup spec.
 */
test.describe("terminal-visual", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("bezel chrome renders with ID plate, screws, and brand stamp", async ({
    page,
  }) => {
    // Bezel elements should be present even before starting a game
    await expect(page.locator("#terminal")).toBeVisible();
    await expect(page.locator("#bezel-plate")).toBeVisible();
    await expect(page.locator("#bezel-plate")).toContainText("МИР-2");
    await expect(page.locator("#bezel-plate")).toContainText("MIR-2 STATION");
    await expect(page.locator("#bezel-plate")).toContainText("CONSOLE 04");
    await expect(page.locator("#bezel-plate")).toContainText("KOVAL");

    // Corner screws
    await expect(page.locator(".screw.tl")).toBeVisible();
    await expect(page.locator(".screw.tr")).toBeVisible();
    await expect(page.locator(".screw.bl")).toBeVisible();
    await expect(page.locator(".screw.br")).toBeVisible();

    // Bottom strip: power LED + brand
    await expect(page.locator("#power-led")).toBeVisible();
    await expect(page.locator("#brand")).toContainText("ЭЛЕКТРОНИКА");
    await expect(page.locator("#brand")).toContainText("МС-0511");
  });

  test("phosphor screen renders 80×25 grid with box-drawing borders", async ({
    page,
  }) => {
    await startNewGame(page);

    const display = page.locator("#display");
    // Wait for the display to be populated (interpreter takes a moment)
    await expect(display).toContainText("╔", { timeout: 10_000 });

    // The display should contain box-drawing characters
    const text = await display.textContent();
    expect(text).toContain("╔");
    expect(text).toContain("╗");
    expect(text).toContain("╚");
    expect(text).toContain("╝");
    expect(text).toContain("║");
    expect(text).toContain("═");
    // Story/sidebar separator junctions
    expect(text).toContain("╤");
    expect(text).toContain("╧");
    // Light vertical divider between columns
    expect(text).toContain("│");
  });

  test("sidebar shows VITALS, SYSTEMS, and INVENTORY sections", async ({
    page,
  }) => {
    await startNewGame(page);

    const text = await page.locator("#display").textContent();
    // Bilingual section headers
    expect(text).toContain("VITALS");
    expect(text).toContain("СОСТОЯНИЕ");
    expect(text).toContain("SYSTEMS");
    expect(text).toContain("СИСТЕМЫ");
    expect(text).toContain("INVENTORY");
    expect(text).toContain("ИНВЕНТАРЬ");
    // O2 and morale gauges
    expect(text).toContain("O2 LEVEL");
    expect(text).toContain("MORALE");
    // System lamps
    expect(text).toContain("PWR");
    expect(text).toContain("LIFE");
    expect(text).toContain("COMM");
    expect(text).toContain("HULL");
  });

  test("header status bar shows SYS, UPT, ORB, TIME", async ({ page }) => {
    await startNewGame(page);

    const text = await page.locator("#display").textContent();
    expect(text).toContain("SYS");
    expect(text).toContain("МИР-2/TERM-04");
    expect(text).toContain("UPT");
    expect(text).toContain("ORB");
    expect(text).toContain("412KM/91.2MIN");
    expect(text).toContain("TIME");
    expect(text).toContain("МСК");
  });

  test("IBM Plex Mono is self-hosted (no Google Fonts CDN)", async ({
    page,
  }) => {
    const html = await page.content();
    // Must NOT contain Google Fonts links
    expect(html).not.toContain("fonts.googleapis.com");
    expect(html).not.toContain("fonts.gstatic.com");

    // CSS must reference local font files
    const css = await page.evaluate(() => {
      const sheets = Array.from(document.styleSheets);
      let rules = "";
      for (const sheet of sheets) {
        try {
          for (const rule of sheet.cssRules) {
            rules += rule.cssText + "\n";
          }
        } catch (_) {
          // cross-origin sheets throw
        }
      }
      return rules;
    });
    expect(css).toContain("IBMPlexMono-Regular.woff2");
    expect(css).toContain("IBMPlexMono-Medium.woff2");
    expect(css).toContain("IBMPlexMono-SemiBold.woff2");
  });

  test("phosphor color palette matches spec", async ({ page }) => {
    const vars = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return {
        screenBg: style.getPropertyValue("--screen-bg").trim(),
        phosphor: style.getPropertyValue("--phosphor").trim(),
        phosphorDim: style.getPropertyValue("--phosphor-dim").trim(),
        phosphorBright: style.getPropertyValue("--phosphor-bright").trim(),
        lampRed: style.getPropertyValue("--lamp-red").trim(),
        lampAmber: style.getPropertyValue("--lamp-amber").trim(),
        lampGreen: style.getPropertyValue("--lamp-green").trim(),
        bezelPaint: style.getPropertyValue("--bezel-paint").trim(),
      };
    });

    expect(vars.screenBg).toBe("#0a1408");
    expect(vars.phosphor).toBe("#6cf06b");
    expect(vars.phosphorDim).toBe("#3a8a39");
    expect(vars.phosphorBright).toBe("#b6ffb5");
    expect(vars.lampRed).toBe("#ff4530");
    expect(vars.lampAmber).toBe("#ffb020");
    expect(vars.lampGreen).toBe("#4dff60");
    expect(vars.bezelPaint).toBe("#6b7560");
  });

  test("scanline overlay and vignette are present", async ({ page }) => {
    await expect(page.locator("#screen")).toBeVisible();
    await expect(page.locator("#scan-line")).toBeAttached();
  });

  test("old three-pane layout elements are removed", async ({ page }) => {
    // The old sidebar, scene panel, and status panel should not exist
    // as visible interactive elements
    await expect(page.locator("#sidebar")).toHaveCount(0);
    await expect(page.locator("#scene-panel")).toHaveCount(0);
    await expect(page.locator("#status-panel")).toHaveCount(0);
    await expect(page.locator("#scene-art")).toHaveCount(0);
  });
});

/**
 * Bezel version display (m13 #198).
 *
 * `scripts/make_version.py` produces `game/dist/version.json` on every
 * build. `ui.js` fetches that file and renders the version string into
 * `#bezel-version`, with an optional ` · <branch>` suffix when the
 * branch isn't `develop` / `main` / etc. — so a side-by-side reviewer
 * can tell at a glance which feature branch is being played.
 */

import { expect, test } from "@playwright/test";

test.describe("bezel version display", () => {
  test("element exists in the bezel brand block", async ({ page }) => {
    await page.goto("/play.html");
    await page.locator("#bezel-version").waitFor({ state: "attached" });
    // Sits inside #brand inside #bezel-bottom.
    const inBrand = await page.evaluate(() => {
      const el = document.getElementById("bezel-version");
      return !!el && !!el.closest("#brand") && !!el.closest("#bezel-bottom");
    });
    expect(inBrand).toBe(true);
  });

  test("renders FW <version> once version.json loads", async ({ page }) => {
    await page.goto("/play.html");
    await page
      .locator("#bezel-version")
      .filter({ hasText: /^FW / })
      .waitFor({ timeout: 5_000 });
    const label = await page.locator("#bezel-version").textContent();
    expect(label).toMatch(/^FW \d+\.\d+\.\d+\+[0-9a-f]+/);
  });

  test("appends branch suffix when not on develop/main", async ({ page }) => {
    // Intercept the version.json fetch so we don't depend on the actual
    // git state of the test runner — the renderer logic is what's
    // under test, not whether CI is on develop.
    await page.route("**/dist/version.json", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          semver: "0.1.0",
          git_sha: "abc1234",
          git_branch: "feature/m13-i198-f_bezel_version_display",
          dirty: false,
          version_string: "0.1.0+abc1234",
        }),
      }),
    );
    await page.goto("/play.html");
    await page
      .locator("#bezel-version")
      .filter({ hasText: /·/ })
      .waitFor({ timeout: 5_000 });
    const label = await page.locator("#bezel-version").textContent();
    expect(label).toBe(
      "FW 0.1.0+abc1234 · feature/m13-i198-f_bezel_version_display",
    );
  });

  test("no branch suffix on develop", async ({ page }) => {
    await page.route("**/dist/version.json", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          semver: "0.1.0",
          git_sha: "def5678",
          git_branch: "develop",
          dirty: false,
          version_string: "0.1.0+def5678",
        }),
      }),
    );
    await page.goto("/play.html");
    await page
      .locator("#bezel-version")
      .filter({ hasText: /^FW / })
      .waitFor({ timeout: 5_000 });
    const label = await page.locator("#bezel-version").textContent();
    expect(label).toBe("FW 0.1.0+def5678");
    expect(label).not.toContain("·");
  });

  test("element hides itself when version.json is missing", async ({
    page,
  }) => {
    await page.route("**/dist/version.json", (route) =>
      route.fulfill({ status: 404 }),
    );
    await page.goto("/play.html");
    await page.locator("#bezel-version").waitFor({ state: "attached" });
    // Give loadVersionJson a moment to fail-quietly.
    await page.waitForTimeout(200);
    const text = await page.locator("#bezel-version").textContent();
    expect(text).toBe("");
    // CSS rule `#brand .version:empty { display: none; }` should hide it.
    const display = await page
      .locator("#bezel-version")
      .evaluate((el) => getComputedStyle(el).display);
    expect(display).toBe("none");
  });
});

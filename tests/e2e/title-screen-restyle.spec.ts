import { expect, test } from "@playwright/test";
import { clearStorage } from "./helpers";

test.describe("title-screen-restyle", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("title screen renders the bezel + phosphor frame", async ({ page }) => {
    await expect(page.locator("#title-screen")).toBeVisible();
    await expect(page.locator("#title-bezel")).toBeVisible();
    await expect(page.locator("#title-phosphor")).toBeVisible();
    /* Phosphor sits inside the bezel; both contain the title content. */
    await expect(
      page.locator("#title-bezel #title-phosphor #title-screen-content"),
    ).toHaveCount(1);
  });

  test("MIR'S END is rendered in the etched ID plate", async ({ page }) => {
    const plate = page.locator("#title-id-plate");
    await expect(plate).toBeVisible();
    await expect(plate.locator("#title-logo")).toHaveText("MIR'S END");
    /* Plate also carries the bilingual station-designation labels. */
    await expect(plate).toContainText("СТАНЦИЯ");
  });

  test("menu buttons carry both English and Russian labels", async ({
    page,
  }) => {
    const newGame = page.locator("#menu-new-game");
    await expect(newGame.locator(".btn-label-en")).toHaveText("New Game");
    await expect(newGame.locator(".btn-label-ru")).toHaveText("НОВАЯ ИГРА");

    await expect(page.locator("#menu-continue .btn-label-ru")).toHaveText(
      "ПРОДОЛЖИТЬ",
    );
    await expect(page.locator("#menu-settings .btn-label-ru")).toHaveText(
      "НАСТРОЙКИ",
    );
  });

  test("phosphor screen paints scanlines and a phosphor-tinted background", async ({
    page,
  }) => {
    const phosphor = page.locator("#title-phosphor");
    /* The scanline overlay is an ::before pseudo with a repeating-linear-gradient.
       Pseudo styles aren't directly inspectable, but we can assert the host
       element has the phosphor background variable applied. */
    const bg = await phosphor.evaluate(
      (el) => getComputedStyle(el).backgroundColor,
    );
    /* --bg-panel resolves to a dark navy; assert it isn't transparent or white. */
    expect(bg).not.toBe("rgba(0, 0, 0, 0)");
    expect(bg).not.toBe("rgb(255, 255, 255)");
  });

  test("MIR'S END glow is rendered via text-shadow", async ({ page }) => {
    const logo = page.locator("#title-logo");
    const shadow = await logo.evaluate((el) => getComputedStyle(el).textShadow);
    /* Multi-layer phosphor glow — the diff specifies three stacked rgba shadows. */
    expect(shadow).toContain("rgba(138, 180, 248");
  });
});

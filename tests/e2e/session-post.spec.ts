import { expect, test } from "@playwright/test";
import { clearStorage, sendCommand, startNewGame } from "./helpers";

/**
 * Verify that the browser POSTs completed sessions to /v1/sessions
 * on game end and manual export, with correct player_kind tagging
 * and graceful failure handling.
 */
test.describe("session-post", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("manual export POSTs session to /v1/sessions", async ({ page }) => {
    const posts: any[] = [];
    await page.route("**/v1/sessions", async (route) => {
      const req = route.request();
      if (req.method() === "POST") {
        posts.push(JSON.parse(req.postData() || "{}"));
        await route.fulfill({ status: 200, body: "{}" });
      } else {
        await route.continue();
      }
    });

    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await page.waitForTimeout(500);

    // Trigger export via Ctrl+E — download still happens, POST is side effect
    const [_download] = await Promise.all([
      page.waitForEvent("download"),
      page.keyboard.press("Control+e"),
    ]);

    // Wait briefly for the async POST
    await page.waitForTimeout(500);

    expect(posts.length).toBe(1);
    const payload = posts[0];
    expect(payload.session_id).toBeTruthy();
    expect(payload.session_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/,
    );
    expect(payload.player_kind).toBe("human");
    expect(payload.game_version).toBeTruthy();
    expect(payload.started_at).toBeTruthy();
    expect(payload.ended_at).toBeTruthy();
    expect(payload.command_history).toContain("open emergency locker");
    expect(payload.transcript.length).toBeGreaterThan(0);
    expect(payload.final_state).toBeTruthy();
  });

  test("game end triggers a POST with completed status", async ({ page }) => {
    const posts: any[] = [];
    await page.route("**/v1/sessions", async (route) => {
      const req = route.request();
      if (req.method() === "POST") {
        posts.push(JSON.parse(req.postData() || "{}"));
        await route.fulfill({ status: 200, body: "{}" });
      } else {
        await route.continue();
      }
    });

    await startNewGame(page);

    // Simulate game-end text by injecting it via the public API
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText("[Game ended]");
    });

    await page.waitForTimeout(500);

    expect(posts.length).toBe(1);
    expect(posts[0].status).toBe("completed");
    expect(posts[0].session_id).toBeTruthy();
  });

  test("server 500 does not crash the game", async ({ page }) => {
    const consoleLogs: string[] = [];
    page.on("console", (msg) => {
      consoleLogs.push(msg.text());
    });

    await page.route("**/v1/sessions", async (route) => {
      await route.fulfill({
        status: 500,
        body: "Internal Server Error",
      });
    });

    await startNewGame(page);
    await sendCommand(page, "open emergency locker");
    await page.waitForTimeout(500);

    // Trigger export — game should not break
    const [_download] = await Promise.all([
      page.waitForEvent("download"),
      page.keyboard.press("Control+e"),
    ]);

    await page.waitForTimeout(500);

    // Game is still interactive after the failed POST
    const storyText = await page
      .locator("#story-output")
      .textContent()
      .then((t) => t ?? "");
    expect(storyText.length).toBeGreaterThan(0);

    // Console should contain a warning log about the 500
    const hasWarnLog = consoleLogs.some(
      (l) => l.includes("Session POST") && l.includes("500"),
    );
    expect(hasWarnLog).toBe(true);
  });

  test("player_kind defaults to 'human' when nothing is set", async ({
    page,
  }) => {
    const posts: any[] = [];
    await page.route("**/v1/sessions", async (route) => {
      const req = route.request();
      if (req.method() === "POST") {
        posts.push(JSON.parse(req.postData() || "{}"));
        await route.fulfill({ status: 200, body: "{}" });
      } else {
        await route.continue();
      }
    });

    await startNewGame(page);

    // Trigger via simulated game end
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText("[Game ended]");
    });
    await page.waitForTimeout(500);

    expect(posts.length).toBe(1);
    expect(posts[0].player_kind).toBe("human");
  });

  test("MIRSEND_PLAYER_KIND init script overrides player_kind", async ({
    page,
  }) => {
    // Set via addInitScript before navigation, like Playwright tests do
    await page.addInitScript(() => {
      (window as any).MIRSEND_PLAYER_KIND = "test:canonical-arc";
    });

    const posts: any[] = [];
    await page.route("**/v1/sessions", async (route) => {
      const req = route.request();
      if (req.method() === "POST") {
        posts.push(JSON.parse(req.postData() || "{}"));
        await route.fulfill({ status: 200, body: "{}" });
      } else {
        await route.continue();
      }
    });

    await startNewGame(page);

    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText("[Game ended]");
    });
    await page.waitForTimeout(500);

    expect(posts.length).toBe(1);
    expect(posts[0].player_kind).toBe("test:canonical-arc");
  });
});

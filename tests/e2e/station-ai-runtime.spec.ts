import { expect, test } from "@playwright/test";
import { clearStorage } from "./helpers";

/**
 * Station AI runtime e2e tests.
 *
 * These tests mock the proxy server (localhost:8787) via Playwright's
 * route interception and verify the full runtime path: command in,
 * prompt built, response routed to the story panel.
 */
test.describe("station-ai-runtime", () => {
  test.beforeEach(async ({ page }) => {
    // Enable warm AI before play.html loads so the runtime path runs
    // instead of the feature-flag canned-line fallback.
    await page.addInitScript(() => {
      (window as Window & { MIRSEND_AI_ENABLED?: number }).MIRSEND_AI_ENABLED =
        1;
      // Suppress the first-run AI onboarding modal so it does not
      // intercept clicks on the menu.
      try {
        localStorage.setItem("mirsend_ai_onboarding_seen", "1");
      } catch (_e) {
        /* storage may be locked before page load; harmless. */
      }
    });
    await page.goto("/play.html");
    await page.evaluate(() => {
      try {
        localStorage.setItem("mirsend_ai_onboarding_seen", "1");
      } catch (_e) {
        /* ignore */
      }
    });
    await clearStorage(page);
    // Re-set after clearStorage in case it wiped this key.
    await page.evaluate(() => {
      localStorage.setItem("mirsend_ai_onboarding_seen", "1");
    });
  });

  test("AI-PROMPT tag is intercepted and triggers proxy call", async ({
    page,
  }) => {
    // Mock the proxy endpoint
    let capturedPayload: any = null;
    await page.route("**/v1/call", async (route) => {
      capturedPayload = JSON.parse(route.request().postData() || "{}");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ text: "Systems nominal, Cosmonaut." }),
      });
    });

    // Start the game
    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    // Simulate an AI-PROMPT tag arriving in the story output
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText(
        "[AI-PROMPT: topic=systems text=How are the systems?]",
      );
    });

    // Wait for the response to render
    await page
      .locator("#story-output .argon-speech")
      .waitFor({ timeout: 5000 });

    // Verify the response appeared with correct styling
    const speech = page.locator("#story-output .argon-speech");
    await expect(speech).toBeVisible();
    await expect(speech.locator(".argon-label")).toHaveText("ARGON-87: ");
    await expect(speech.locator(".argon-text")).toHaveText(
      "Systems nominal, Cosmonaut.",
    );

    // Verify the proxy was called with correct payload
    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.role).toBe("station-ai");
    expect(capturedPayload.player_input).toBe("How are the systems?");
    expect(capturedPayload.game_state).toBeDefined();
    expect(capturedPayload.conversation_history).toEqual([]);
  });

  test("fallback message on proxy failure", async ({ page }) => {
    // Mock the proxy to return an error
    await page.route("**/v1/call", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      });
    });

    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    // Simulate an AI-PROMPT tag
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText(
        "[AI-PROMPT: topic=status text=Talk to me]",
      );
    });

    // Fallback prints the canned line as plain narration, not as Argon speech.
    await page
      .locator("#story-output")
      .filter({ hasText: "runtime is not attached" })
      .waitFor({ timeout: 5000 });
  });

  test("fallback message on network failure", async ({ page }) => {
    // Mock the proxy to abort (simulate network down)
    await page.route("**/v1/call", async (route) => {
      await route.abort("connectionrefused");
    });

    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText("[AI-PROMPT: text=Hello Argon]");
    });

    await page
      .locator("#story-output")
      .filter({ hasText: "runtime is not attached" })
      .waitFor({ timeout: 5000 });
  });

  test("conversation history accumulates across calls", async ({ page }) => {
    let callCount = 0;
    let lastPayload: any = null;

    await page.route("**/v1/call", async (route) => {
      lastPayload = JSON.parse(route.request().postData() || "{}");
      callCount++;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ text: `Response ${callCount}` }),
      });
    });

    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    // First call
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText(
        "[AI-PROMPT: text=First question]",
      );
    });
    await page
      .locator("#story-output .argon-speech")
      .first()
      .waitFor({ timeout: 5000 });

    // Second call
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText(
        "[AI-PROMPT: text=Second question]",
      );
    });
    await page.waitForTimeout(1000);

    // The second call should include conversation history from the first
    expect(callCount).toBe(2);
    expect(lastPayload.conversation_history).toHaveLength(2);
    expect(lastPayload.conversation_history[0].role).toBe("player");
    expect(lastPayload.conversation_history[0].content).toBe("First question");
    expect(lastPayload.conversation_history[1].role).toBe("argon");
    expect(lastPayload.conversation_history[1].content).toBe("Response 1");
  });

  test("conversation history resets on new game", async ({ page }) => {
    await page.route("**/v1/call", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ text: "Hello." }),
      });
    });

    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    // Make a call to build up history
    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText("[AI-PROMPT: text=Hello]");
    });
    await page
      .locator("#story-output .argon-speech")
      .first()
      .waitFor({ timeout: 5000 });

    // Verify history exists
    const history = await page.evaluate(() => {
      return (window as any).StationAI.getConversationHistory();
    });
    expect(history.length).toBe(2);

    // Reset via new game
    await page.evaluate(() => {
      (window as any).StationAI.resetConversation();
    });

    const afterReset = await page.evaluate(() => {
      return (window as any).StationAI.getConversationHistory();
    });
    expect(afterReset.length).toBe(0);
  });

  test("AI-PROMPT tag is suppressed from story display", async ({ page }) => {
    await page.route("**/v1/call", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ text: "Acknowledged." }),
      });
    });

    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText(
        "[AI-PROMPT: text=Status report]",
      );
    });

    await page
      .locator("#story-output .argon-speech")
      .waitFor({ timeout: 5000 });

    // The raw tag should not appear in the story output
    const text = await page.locator("#story-output").textContent();
    expect(text).not.toContain("[AI-PROMPT");
  });

  test("state-affecting tags are parsed and stripped from display", async ({
    page,
  }) => {
    await page.route("**/v1/call", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          text: "Trust is earned. [AI-SET: player-trusts-argon true] Consider this a beginning.",
        }),
      });
    });

    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      (window as any).MirsEnd.appendStoryText("[AI-PROMPT: text=I trust you]");
    });

    await page
      .locator("#story-output .argon-speech")
      .waitFor({ timeout: 5000 });

    // The state tag should be stripped from display
    const speechText = await page
      .locator("#story-output .argon-speech .argon-text")
      .textContent();
    expect(speechText).not.toContain("[AI-SET");
    expect(speechText).toContain("Trust is earned");
    expect(speechText).toContain("Consider this a beginning");
  });

  test("parseStateEffectTags extracts all tag types", async ({ page }) => {
    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    const effects = await page.evaluate(() => {
      return (window as any).StationAI.parseStateEffectTags(
        "Hello [AI-SET: trust-level high] world [AI-REVEAL: hidden-room] and [AI-NUDGE: restore-power] done",
      );
    });

    expect(effects).toHaveLength(3);
    expect(effects[0]).toEqual({
      type: "set",
      key: "trust-level",
      value: "high",
    });
    expect(effects[1]).toEqual({
      type: "reveal",
      key: "hidden-room",
      value: true,
    });
    expect(effects[2]).toEqual({
      type: "nudge",
      key: "restore-power",
      value: true,
    });
  });

  test("stripStateTags removes all tag types", async ({ page }) => {
    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    const stripped = await page.evaluate(() => {
      return (window as any).StationAI.stripStateTags(
        "Before [AI-SET: key value] middle [AI-REVEAL: room] after [AI-NUDGE: hint] end",
      );
    });

    expect(stripped).not.toContain("[AI-SET");
    expect(stripped).not.toContain("[AI-REVEAL");
    expect(stripped).not.toContain("[AI-NUDGE");
    expect(stripped).toContain("Before");
    expect(stripped).toContain("end");
  });

  test("matchAiPromptTag parses various formats", async ({ page }) => {
    await page.click("#menu-new-game");
    await page.waitForTimeout(300);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    // Full format
    const full = await page.evaluate(() => {
      return (window as any).StationAI.matchAiPromptTag(
        "[AI-PROMPT: topic=systems text=How are the systems?]",
      );
    });
    expect(full).not.toBeNull();
    expect(full.topic).toBe("systems");
    expect(full.text).toBe("How are the systems?");

    // Text only
    const textOnly = await page.evaluate(() => {
      return (window as any).StationAI.matchAiPromptTag(
        "[AI-PROMPT: text=Hello Argon]",
      );
    });
    expect(textOnly).not.toBeNull();
    expect(textOnly.text).toBe("Hello Argon");

    // Bare tag
    const bare = await page.evaluate(() => {
      return (window as any).StationAI.matchAiPromptTag("[AI-PROMPT]");
    });
    expect(bare).not.toBeNull();

    // Non-matching
    const none = await page.evaluate(() => {
      return (window as any).StationAI.matchAiPromptTag(
        "Just a regular line of text",
      );
    });
    expect(none).toBeNull();
  });
});

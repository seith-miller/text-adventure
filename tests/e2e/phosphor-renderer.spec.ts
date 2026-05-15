/**
 * 80-column phosphor renderer (m13 #143).
 *
 * Drives `window.MirsEnd` directly so the test exercises the renderer
 * without spinning up the full Glulx interpreter on every assertion.
 * Covers the four behaviors that distinguish #143 from the broader
 * Soviet-terminal port that landed via #151:
 *
 *   - word-wrap of prose at STORY_W = 48
 *   - dim `<echo>> command</echo>` line for player input
 *   - bilingual Latin/Cyrillic heading on known room names
 *   - scroll-pin: appended lines do not yank a scrolled-up viewport
 */

import { expect, test } from "@playwright/test";

test.describe("phosphor renderer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await page.waitForFunction(
      () =>
        (window as any).MirsEnd?.appendStoryText !== undefined &&
        (window as any).MirsEnd?.scrollUp !== undefined,
    );
  });

  test("word-wraps long prose into the 48-char story column", async ({
    page,
  }) => {
    const longLine =
      "The lamp on the bulkhead hums against the dark, throwing pale phosphor across the steel as your breath fogs in the cold air of the module.";
    await page.evaluate(
      (t) => (window as any).MirsEnd.appendStoryText(t),
      longLine,
    );
    const display = (await page.locator("#display").textContent()) ?? "";
    const proseLines = display
      .split("\n")
      .filter(
        (l) =>
          l.includes("lamp") ||
          l.includes("bulkhead") ||
          l.includes("phosphor") ||
          l.includes("module"),
      );
    // Word-wrap should produce more than one line of body content.
    expect(proseLines.length).toBeGreaterThanOrEqual(2);
  });

  test("echoes player input as a dim `> command` line", async ({ page }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.appendPlayerInput("examine console"),
    );
    const html = await page.locator("#display").innerHTML();
    expect(html).toContain("<echo>&gt; examine console</echo>");
  });

  test("renders Latin/Cyrillic shadow heading on a known room name", async ({
    page,
  }) => {
    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText("Crew Quarters"),
    );
    const display = (await page.locator("#display").textContent()) ?? "";
    expect(display).toContain("CREW QUARTERS");
    expect(display).toContain("ОТСЕК ЭКИПАЖА");
  });

  test("scroll-pin: appended lines do not yank a scrolled-up viewport", async ({
    page,
  }) => {
    // Fill the buffer well past BODY_ROWS (19) so scrollback is meaningful.
    await page.evaluate(() => {
      const M = (window as any).MirsEnd;
      for (let i = 0; i < 60; i++) {
        M.appendStoryText(`Line number ${i} of the story buffer.`);
      }
    });

    await page.evaluate(() => (window as any).MirsEnd.scrollUp(5));
    const offsetBefore = await page.evaluate(() =>
      (window as any).MirsEnd.getScrollOffset(),
    );
    expect(offsetBefore).toBeGreaterThan(0);

    await page.evaluate(() =>
      (window as any).MirsEnd.appendStoryText(
        "BEACON: A new line arrives later.",
      ),
    );

    const offsetAfter = await page.evaluate(() =>
      (window as any).MirsEnd.getScrollOffset(),
    );
    // Offset should grow by the number of lines appended so the visible
    // window stays anchored on the same content.
    expect(offsetAfter).toBeGreaterThan(offsetBefore);

    const visibleAfter = (await page.locator("#display").textContent()) ?? "";
    expect(visibleAfter).not.toContain("BEACON");

    // Returning to the bottom shows the new line.
    await page.evaluate(() => (window as any).MirsEnd.scrollToBottom());
    const visibleAtBottom =
      (await page.locator("#display").textContent()) ?? "";
    expect(visibleAtBottom).toContain("BEACON");
    const offsetAtBottom = await page.evaluate(() =>
      (window as any).MirsEnd.getScrollOffset(),
    );
    expect(offsetAtBottom).toBe(0);
  });
});

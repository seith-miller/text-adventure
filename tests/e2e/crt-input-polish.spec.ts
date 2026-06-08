/**
 * CRT input polish (m13 #133).
 *
 * Covers the four polish behaviors that distinguish the new terminal
 * input row from the old plain-phosphor textbox:
 *
 *   - typed text renders inside <bri> phosphor with a blinking <cur> █
 *   - submitted commands echo as a dim `> command` line
 *   - up/down arrow keys cycle command history without booting the
 *     interpreter (the renderer reacts to ui.js state directly)
 *   - command history persists across page reloads via localStorage
 *
 * Like phosphor-renderer.spec.ts, this drives `window.MirsEnd` and the
 * visible #command-input directly so we don't depend on Quixe being
 * loaded; the focus here is the renderer + input wiring.
 */

import { expect, test } from "@playwright/test";

const HISTORY_KEY = "mirsend_command_history";

test.describe("crt input polish", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.appendPlayerInput !== undefined,
    );
  });

  test("typed text renders inside <bri> phosphor with a blinking cursor", async ({
    page,
  }) => {
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.value = "examine console";
      input.dispatchEvent(new Event("input"));
    });
    const html = await page.locator("#display").innerHTML();
    // Both the `>` prompt and the typed text share one <bri> wrapper.
    expect(html).toContain("<bri>&gt; examine console</bri>");
    // Cursor is a blinking <cur> block immediately after the input.
    expect(html).toMatch(/<cur>█<\/cur>/);
  });

  test("empty input still shows the bright prompt and the cursor", async ({
    page,
  }) => {
    const html = await page.locator("#display").innerHTML();
    expect(html).toContain("<bri>&gt; </bri>");
    expect(html).toMatch(/<cur>█<\/cur>/);
  });

  test("Enter writes a dim echo line and clears the input row", async ({
    page,
  }) => {
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.value = "look";
      input.dispatchEvent(new Event("input"));
      input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
      );
    });

    const html = await page.locator("#display").innerHTML();
    // Dim echo of the submitted command lands in the story column.
    expect(html).toContain("<echo>&gt; look</echo>");
    // Input row is back to the empty prompt + cursor.
    expect(html).toContain("<bri>&gt; </bri>");
  });

  test("up/down cycles through prior commands", async ({ page }) => {
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      const submit = (cmd: string) => {
        input.value = cmd;
        input.dispatchEvent(new Event("input"));
        input.dispatchEvent(
          new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
        );
      };
      submit("look");
      submit("inventory");
      submit("north");
    });

    // ArrowUp pulls the most-recent command into the input.
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true }),
      );
    });
    let value = await page.locator("#command-input").inputValue();
    expect(value).toBe("north");

    // Another ArrowUp pulls the one before that.
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true }),
      );
    });
    value = await page.locator("#command-input").inputValue();
    expect(value).toBe("inventory");

    // ArrowDown walks back forward.
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }),
      );
    });
    value = await page.locator("#command-input").inputValue();
    expect(value).toBe("north");

    // One more ArrowDown lands on the empty live input.
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }),
      );
    });
    value = await page.locator("#command-input").inputValue();
    expect(value).toBe("");
  });

  test("identical consecutive commands de-dupe in history", async ({
    page,
  }) => {
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      const submit = (cmd: string) => {
        input.value = cmd;
        input.dispatchEvent(new Event("input"));
        input.dispatchEvent(
          new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
        );
      };
      submit("look");
      submit("look");
      submit("look");
    });

    const history = await page.evaluate(
      () => (window as any).MirsEnd.getState().commandHistory,
    );
    expect(history).toEqual(["look"]);
  });

  test("command history persists across page reloads", async ({ page }) => {
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      const submit = (cmd: string) => {
        input.value = cmd;
        input.dispatchEvent(new Event("input"));
        input.dispatchEvent(
          new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
        );
      };
      submit("examine console");
      submit("open locker");
    });

    const persisted = await page.evaluate(
      (k) => localStorage.getItem(k),
      HISTORY_KEY,
    );
    expect(persisted).not.toBeNull();
    expect(JSON.parse(persisted ?? "[]")).toEqual([
      "examine console",
      "open locker",
    ]);

    await page.reload();
    await page.waitForFunction(
      () => (window as any).MirsEnd?.getState !== undefined,
    );

    const restored = await page.evaluate(
      () => (window as any).MirsEnd.getState().commandHistory,
    );
    expect(restored).toEqual(["examine console", "open locker"]);

    // After reload, ArrowUp surfaces the last-recalled command from the
    // persisted history — the player picks up where they left off.
    await page.evaluate(() => {
      const input = document.getElementById(
        "command-input",
      ) as HTMLInputElement;
      input.focus();
      input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true }),
      );
    });
    const value = await page.locator("#command-input").inputValue();
    expect(value).toBe("open locker");
  });
});

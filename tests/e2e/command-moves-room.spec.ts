import { expect, test } from "@playwright/test";
import {
  asMirsEnd,
  clearStorage,
  sendCommand,
  startNewGame,
  waitForStoryText,
} from "./helpers";

test.describe("command-moves-room", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/play.html");
    await clearStorage(page);
  });

  test("typing a command drives the interpreter and emits new text", async ({
    page,
  }) => {
    await startNewGame(page);

    // The player starts in darkness. "open emergency locker" is the first
    // valid action; the interpreter should echo a recognizable response.
    await sendCommand(page, "open emergency locker");
    await waitForStoryText(page, /flashlight|locker/i);

    const history = (await asMirsEnd(page)).commandHistory;
    expect(history).toContain("open emergency locker");
  });

  test("room transitions are reflected in state.currentRoom", async ({
    page,
  }) => {
    await startNewGame(page);

    // Drive the full sequence to the Main Corridor. Each sendCommand
    // polls until the interpreter's next response lands, keyed off
    // commandHistory growth rather than fragile text matching.
    const commands = [
      "open emergency locker",
      "take chemical flashlight",
      "switch on chemical flashlight",
      "north",
    ];
    let expected = (await asMirsEnd(page)).commandHistory.length;
    for (const cmd of commands) {
      await sendCommand(page, cmd);
      expected += 1;
      await expect
        .poll(async () => (await asMirsEnd(page)).commandHistory.length, {
          timeout: 5_000,
          message: `waiting for "${cmd}" to be processed`,
        })
        .toBe(expected);
    }

    // Wait for Main Corridor text to appear in the story panel.
    await expect(page.locator("#story-output")).toContainText(
      /Main Corridor/i,
      {
        timeout: 5_000,
      },
    );

    // ui.js mirrors detected room names onto state.currentRoom.
    await expect
      .poll(
        async () => (await asMirsEnd(page)).currentRoom?.toLowerCase() ?? "",
        {
          timeout: 3_000,
        },
      )
      .toContain("main corridor");
  });
});

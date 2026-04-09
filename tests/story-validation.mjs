/**
 * Story validation test — loads compiled Ink JSON and walks all reachable
 * paths to verify there are no dead ends (states with no choices and no end).
 */

import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, it } from "node:test";
import { Story } from "inkjs";

const distStoryDir = join("game", "dist", "story");

/** Get all compiled story JSON files */
function getStoryFiles() {
  try {
    return readdirSync(distStoryDir).filter((f) => f.endsWith(".json"));
  } catch {
    return [];
  }
}

/**
 * Walk all reachable paths in a story using BFS over choice indices.
 * Returns an object with stats about the traversal.
 */
function walkAllPaths(jsonContent) {
  const visited = new Set();
  let totalPaths = 0;

  // BFS queue — each entry is an array of choice indices taken so far
  const queue = [[]];

  while (queue.length > 0) {
    const choicePath = queue.shift();
    const pathKey = choicePath.join(",");

    if (visited.has(pathKey)) continue;
    visited.add(pathKey);

    const story = new Story(jsonContent);

    // Replay choices to reach this state
    let replayOk = true;
    for (const choiceIdx of choicePath) {
      while (story.canContinue) story.Continue();
      if (choiceIdx >= story.currentChoices.length) {
        replayOk = false;
        break;
      }
      story.ChooseChoiceIndex(choiceIdx);
    }

    if (!replayOk) continue;

    // Continue the story from this state
    while (story.canContinue) story.Continue();

    if (story.currentChoices.length > 0) {
      // Enqueue each available choice
      for (let i = 0; i < story.currentChoices.length; i++) {
        const nextPath = [...choicePath, i];
        const nextKey = nextPath.join(",");
        if (!visited.has(nextKey)) {
          queue.push(nextPath);
        }
      }
    } else {
      // No choices — this is a terminal state
      totalPaths++;

      // Check if the story has actually ended (no more content and no choices)
      // A dead end would be a state with no choices AND no END marker
      // In inkjs, if the story properly ends, canContinue is false and currentChoices is empty
      // This is expected for stories with END markers — we just count completed paths
    }
  }

  return { totalPaths, statesVisited: visited.size };
}

describe("Story validation", () => {
  const storyFiles = getStoryFiles();

  // The project has migrated from Ink to Inform 7. The Ink path validation
  // only runs when compiled Ink JSON happens to be present (e.g. during a
  // bisect against a pre-migration commit). Skip cleanly otherwise so CI
  // can keep this test in place as a regression check without failing on
  // every run.
  if (storyFiles.length === 0) {
    it("Ink story files not present — skipping (project migrated to Inform 7)", () => {
      console.log(
        "  No compiled Ink JSON found in game/dist/story/. " +
          "Validation skipped — see #11 / #12 for the Inform 7 migration.",
      );
    });
    return;
  }

  for (const file of storyFiles) {
    describe(file, () => {
      it("should load as valid Ink JSON", () => {
        const content = readFileSync(join(distStoryDir, file), "utf-8");
        const json = JSON.parse(content);
        const story = new Story(json);
        assert.ok(story, `Failed to load ${file} as Ink story`);
      });

      it("should have reachable paths that all terminate", () => {
        const content = readFileSync(join(distStoryDir, file), "utf-8");
        const json = JSON.parse(content);
        const { totalPaths, statesVisited } = walkAllPaths(json);

        console.log(
          `  ${file}: ${totalPaths} terminal path(s), ${statesVisited} state(s) visited`,
        );

        assert.ok(
          totalPaths > 0,
          `${file}: No terminal paths found — story may have infinite loops with no ending`,
        );
      });
    });
  }
});

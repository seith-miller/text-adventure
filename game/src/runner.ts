// Terminal game runner for the illustrated text adventure
// Loads compiled Ink JSON and presents the story via stdin/stdout

import * as fs from "node:fs";
import * as path from "node:path";
import * as readline from "node:readline";
import { fileURLToPath } from "node:url";
import { Story } from "inkjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROJECT_ROOT = path.resolve(__dirname, "..", "..");

const DEFAULT_STORY_PATH = path.join(
  PROJECT_ROOT,
  "game",
  "dist",
  "story",
  "opening.json",
);

const DEFAULT_ASCII_DIR = path.join(PROJECT_ROOT, "game", "assets", "ascii");

export interface RunnerOptions {
  storyPath?: string;
  asciiDir?: string;
  input?: NodeJS.ReadableStream;
  output?: NodeJS.WritableStream;
}

function loadStory(storyPath: string): Story {
  const json = fs.readFileSync(storyPath, "utf-8");
  return new Story(json);
}

function loadAsciiArt(asciiDir: string, name: string): string | null {
  const filePath = path.join(asciiDir, `${name}.txt`);
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }
}

function processTags(
  tags: string[],
  asciiDir: string,
  log: (msg: string) => void,
): void {
  for (const tag of tags) {
    const match = tag.match(/^\s*ascii:\s*(.+)\s*$/);
    if (match) {
      const art = loadAsciiArt(asciiDir, match[1].trim());
      if (art) {
        log("");
        log(art);
      }
    }
  }
}

function formatStatusLine(story: Story): string | null {
  const oxygen = story.variablesState.oxygen;
  const morale = story.variablesState.morale;
  if (oxygen == null && morale == null) return null;
  const parts: string[] = [];
  if (oxygen != null) parts.push(`O2: ${oxygen}%`);
  if (morale != null) parts.push(`Morale: ${morale}`);
  return `--- [ ${parts.join("  |  ")} ] ---`;
}

/**
 * Creates a line reader that buffers lines from the input stream.
 * Works correctly with both interactive (TTY) and piped input.
 */
function createLineReader(
  input: NodeJS.ReadableStream,
  output: NodeJS.WritableStream,
) {
  const lineBuffer: string[] = [];
  let closed = false;
  let waiting: ((line: string | null) => void) | null = null;

  const rl = readline.createInterface({ input, output, terminal: false });

  rl.on("line", (line: string) => {
    if (waiting) {
      const resolve = waiting;
      waiting = null;
      resolve(line);
    } else {
      lineBuffer.push(line);
    }
  });

  rl.on("close", () => {
    closed = true;
    if (waiting) {
      const resolve = waiting;
      waiting = null;
      resolve(null);
    }
  });

  return {
    nextLine(): Promise<string | null> {
      if (lineBuffer.length > 0) {
        return Promise.resolve(lineBuffer.shift()!);
      }
      if (closed) {
        return Promise.resolve(null);
      }
      return new Promise((resolve) => {
        waiting = resolve;
      });
    },
    close() {
      rl.close();
    },
  };
}

export async function runGame(options: RunnerOptions = {}): Promise<void> {
  const storyPath = options.storyPath ?? DEFAULT_STORY_PATH;
  const asciiDir = options.asciiDir ?? DEFAULT_ASCII_DIR;
  const input = options.input ?? process.stdin;
  const output = options.output ?? process.stdout;

  const story = loadStory(storyPath);
  const reader = createLineReader(input, output);
  const log = (msg: string) => {
    output.write(`${msg}\n`);
  };

  log("");
  log("╔══════════════════════════════════════════╗");
  log("║     ILLUSTRATED TEXT ADVENTURE  v0.1     ║");
  log("╚══════════════════════════════════════════╝");
  log("");

  while (true) {
    // Continue reading story text
    while (story.canContinue) {
      const text = story.Continue()!;
      const tags = story.currentTags;

      if (tags && tags.length > 0) {
        processTags(tags, asciiDir, log);
      }

      const trimmed = text.trim();
      if (trimmed) {
        log(trimmed);
        log("");
      }
    }

    // Show resource status
    const status = formatStatusLine(story);
    if (status) {
      log("");
      log(status);
    }

    // Check for choices
    const choices = story.currentChoices;
    if (choices.length === 0) {
      log("");
      log("═══════════════════════════════════════════");
      log("  The story pauses here... for now.");
      log("  Thank you for playing the prototype.");
      log("═══════════════════════════════════════════");
      log("");
      break;
    }

    // Display choices
    log("");
    for (let i = 0; i < choices.length; i++) {
      log(`  ${i + 1}. ${choices[i].text}`);
    }
    log("");

    // Get player input
    let validChoice = false;
    while (!validChoice) {
      output.write("> ");
      const answer = await reader.nextLine();

      if (answer === null) {
        // Input stream closed (EOF)
        reader.close();
        return;
      }

      const num = parseInt(answer.trim(), 10);
      if (Number.isNaN(num) || num < 1 || num > choices.length) {
        log(`Please enter a number between 1 and ${choices.length}.`);
        continue;
      }

      story.ChooseChoiceIndex(num - 1);
      validChoice = true;
    }
  }

  reader.close();
}

// Run if executed directly
const isDirectRun =
  process.argv[1] &&
  (process.argv[1].endsWith("runner.js") ||
    process.argv[1].endsWith("runner.ts"));

if (isDirectRun) {
  runGame().catch((err: Error) => {
    console.error("Fatal error:", err.message);
    process.exit(1);
  });
}

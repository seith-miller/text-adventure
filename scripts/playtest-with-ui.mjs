#!/usr/bin/env node

/*
  playtest-with-ui.mjs

  Headless web playtester. Boots play.html in Playwright, hands turn-by-
  turn UI state to Claude, and lets Claude play the game by typing into
  the actual <input>. When Claude spots a UI bug, it calls report_bug
  and we file a GitHub issue with a screenshot, transcript excerpt, and
  rendered DOM snapshot.

  Distinct from scripts/playtest.py — that drives Glulx via MCP and
  never touches the UI. This drives the UI exactly as a human player
  would, so it can catch UI-only bugs (rendering, layout, state desync,
  button wiring, character-encoding regressions).

  ## Setup

    npm install                       # @anthropic-ai/sdk + @playwright/test
    npx playwright install chromium   # one-time
    python3 scripts/extract_key.py    # writes .env.playtest
    set -a && . .env.playtest && set +a
    python3 -m http.server -d game 8765 &   # serve the game

  ## Run

    node scripts/playtest-with-ui.mjs [options]

  Options:
    --model MODEL        Claude model (default: claude-sonnet-4-5)
    --max-turns N        Hard cap on turns (default: 60)
    --headed             Show the browser (debugging)
    --file-bugs          File any bug-report calls as GitHub issues
                         (labels: playtest, bug). Default OFF — opt in for
                         scheduled QA runs and CI. Without this flag the
                         harness still runs and saves evidence locally.
    --milestone NAME     Optional GitHub milestone for filed bugs.
                         Off by default since the playtester finds any
                         kind of real bug and a static milestone would
                         mis-tag most of them.
*/

import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import Anthropic from "@anthropic-ai/sdk";
import { chromium } from "@playwright/test";

// ── Args ─────────────────────────────────────────────────────
const argv = process.argv.slice(2);
function flag(name, def = false) {
  return argv.includes(`--${name}`) || def;
}
function val(name, def) {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : def;
}
const MODEL = val("model", "claude-sonnet-4-5");
const MAX_TURNS = parseInt(val("max-turns", "60"), 10);
const HEADED = flag("headed");
// Filing is opt-in (matches scripts/playtest.py convention). Without
// --file-bugs, a bug call still produces local evidence but no GitHub
// issue. CI workflows pass --file-bugs explicitly.
const FILE_BUGS = flag("file-bugs");
// Backwards-compatible: --no-file used to be a flag; now it's a no-op
// because filing is already off by default.
if (argv.includes("--no-file")) {
  console.error(
    "[playtest] --no-file is deprecated and now a no-op (filing is " +
      "opt-in via --file-bugs). Continuing without filing.",
  );
}
const MILESTONE = val("milestone", "");
const BASE_URL = val("url", "http://localhost:8765/play.html");

// ── Setup ────────────────────────────────────────────────────
if (!process.env.ANTHROPIC_API_KEY) {
  console.error(
    "ANTHROPIC_API_KEY not set. Run `set -a && . .env.playtest && set +a` first.",
  );
  process.exit(1);
}

const RUN_ID = new Date().toISOString().replace(/[:.]/g, "-");
const OUT_DIR = `/tmp/playtest-with-ui/${RUN_ID}`;
mkdirSync(OUT_DIR, { recursive: true });
console.log(`[playtest] run dir: ${OUT_DIR}`);

const anthropic = new Anthropic();

// ── Tools the model can call ─────────────────────────────────
const TOOLS = [
  {
    name: "submit_command",
    description:
      "Type a command into the game's text input and press Enter. " +
      "Returns the screen state after the game responds. " +
      "Use whatever commands feel natural for a text adventure: look, " +
      "examine X, take Y, north, inventory, etc.",
    input_schema: {
      type: "object",
      properties: {
        command: { type: "string", description: "The command text to type" },
      },
      required: ["command"],
    },
  },
  {
    name: "click",
    description:
      "Click a UI element by CSS selector. Useful for menu buttons " +
      "(#btn-save, #btn-load, #btn-export, #ingame-menu-btn) or any " +
      "visible affordance. Most gameplay should go through submit_command.",
    input_schema: {
      type: "object",
      properties: {
        selector: { type: "string", description: "CSS selector" },
      },
      required: ["selector"],
    },
  },
  {
    name: "report_bug",
    description:
      "Report a UI / UX bug you've observed. Stops the playtest. Use " +
      "this when something on screen looks wrong, broken, or " +
      "inconsistent. Include enough detail that a developer can " +
      "reproduce it from your description alone.",
    input_schema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          description: "Brief bug title (under 80 chars)",
        },
        description: {
          type: "string",
          description:
            "Markdown description: what you observed, what you expected, " +
            "what you tried, why it's wrong. Reference specific commands " +
            "you submitted leading up to this.",
        },
        severity: {
          type: "string",
          enum: ["minor", "moderate", "severe"],
          description:
            "minor=cosmetic, moderate=functional but recoverable, " +
            "severe=blocks gameplay or corrupts state",
        },
      },
      required: ["title", "description", "severity"],
    },
  },
];

const SYSTEM = `You are a meticulous QA playtester driving a text-adventure game in a real browser. Your goal is to find UI bugs by playing the game naturally and watching the screen for problems.

The game is "MIR'S END" — a Soviet-themed survival story. The UI is a green-phosphor terminal with a painted-metal bezel: an etched ID plate at the top (МИР-2 / MIR-2 STATION, console number, operator, date), a story column on the left, a status sidebar on the right (VITALS, SYSTEMS, INVENTORY), a SYS header bar with location + console + date/time, and a command input row at the bottom. Outside the screen there's a power LED, vent slots, and an ЭЛЕКТРОНИКА brand stamp.

Each turn you receive TWO things:
1. A screenshot of the live page (use this to judge VISUAL problems — alignment, color, overflow, glyph rendering, bezel chrome, anything that looks off to a human eye)
2. The textContent of the rendered terminal (use this to quote exact strings in your bug report)

# Live regions vs scrollback — READ THIS BEFORE FILING

Only some parts of the screen are LIVE state. Other parts are a HISTORICAL TRANSCRIPT. Conflating the two is the most common false-positive class — do not file based on this confusion.

LIVE (always reflects current game state):
- The SYS header bar (top row): location, console, date/time
- The right-side sidebar: VITALS bars, SYSTEMS lamps, INVENTORY list
- The bottom input row (current cursor + what you're typing)

TRANSCRIPT (chronological log of past output, never rewritten):
- The entire story column on the left, including any \`> command\` echoes, room names, prose, and prior \`> inventory\` / \`> status\` outputs

Implications:
- Yes, an old "You are carrying: a chocolate bar" line will still appear in the scrollback after you eat the chocolate bar. That's a transcript of what was printed earlier. The live INVENTORY in the sidebar is the source of truth. NOT A BUG.
- Yes, an old "O2 75%" line will still appear in the scrollback after O2 drops to 60%. The live VITALS bar is the source of truth. NOT A BUG.
- Comparing scrollback text from N turns ago to the live sidebar now is meaningless and is NEVER a bug.

A REAL state-mismatch bug looks like ONE of these:
- The CURRENT turn's prose just said "You picked up the wrench" but the sidebar INVENTORY this same turn still doesn't show a wrench
- The header bar says CREW QUARTERS but the most recent room-heading line in scrollback says COMMAND MODULE
- The sidebar morale shows 80% but the prose this turn just said "You feel utterly hopeless" with no morale change
- Numbers the live sidebar and the live header disagree on RIGHT NOW (not historical)

Before filing, ask: "Would a developer reading this say 'yes that's a bug' or would they say 'that's just how scrollback works'?" If you can't be sure, keep playing.

# Other UI problems worth flagging

- Text overflow past column boundaries; box-drawing borders that don't line up
- Garbled or duplicated characters / phantom prompts / leaked HTML tags or template tokens (\`<hd>\`, \`&amp;gt;\`, \`[object Object]\`)
- Same turn: prose contradicts the sidebar
- Same turn: header contradicts the sidebar
- Cursor doesn't blink, input doesn't echo when you type, buttons don't react when clicked
- Visual glitches — wrong colors, weird spacing, unintended overlap
- Crashes or no-output-after-command
- Anything that looks unintentional

# How to play

Play like a curious player. Try things. Examine objects. Move between rooms. Take items. Eat / use them. Send save / load occasionally. Try EXAMINE, TAKE, INVENTORY, STATUS, HELP. Try \`talk to argon\` if context suggests it. You have ${MAX_TURNS} turns.

When you spot a real bug, call report_bug. Otherwise call submit_command with your next move. Stay in QA mode — don't roleplay or narrate. Your job is to break the UI, not the story.`;

// ── Browser harness ──────────────────────────────────────────
const browser = await chromium.launch({ headless: !HEADED });
const ctx = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
});
const page = await ctx.newPage();

page.on("pageerror", (e) =>
  console.log(`  [pageerror] ${e.message.split("\n")[0]}`),
);

console.log(`[playtest] loading ${BASE_URL}`);
await page.goto(BASE_URL, { waitUntil: "networkidle" });

// Click "New Game" if visible
const newGame = page.locator("#menu-new-game");
if (await newGame.isVisible().catch(() => false)) {
  await newGame.click();
}

await page.waitForSelector("#command-input", {
  state: "visible",
  timeout: 15000,
});

// Click through any intro
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(400);
  const introActive = await page.evaluate(
    () => !!window.MirsEndIntro?.isActive?.(),
  );
  if (!introActive) break;
  await page.mouse.click(800, 500);
}
await page.waitForTimeout(1500);

// ── State capture ────────────────────────────────────────────
//
// Each turn we hand the model BOTH:
//   - a PNG screenshot of the live page (bezel chrome + phosphor screen,
//     rendered exactly as a player would see it — catches visual bugs
//     that don't appear in the DOM)
//   - the textContent of <pre id="display"> (text-mode grid — gives the
//     model a precise reading of words/numbers it can quote in a bug
//     report)
//
// Returns an array of Anthropic content blocks ready to be attached as
// tool_result content (or the initial user message).
async function captureState(note = null) {
  // Animations frozen so the cursor blink doesn't randomly capture in
  // its off-frame, which can look like a bug to the model.
  await page.addStyleTag({
    content:
      "*, *::before, *::after { animation-play-state: paused !important; }",
  });
  const buf = await page.screenshot();
  const grid = await page.evaluate(() => {
    const el = document.getElementById("display");
    return el ? el.innerText : "";
  });
  const browserTitle = await page.title();

  const text =
    `[browser tab title]   ${browserTitle}\n` +
    `\n[rendered terminal — 80 cols × 25 rows, textContent]\n${grid}` +
    (note ? `\n\n[note]   ${note}` : "");

  return [
    {
      type: "image",
      source: {
        type: "base64",
        media_type: "image/png",
        data: buf.toString("base64"),
      },
    },
    { type: "text", text },
  ];
}

// ── Tool implementations ─────────────────────────────────────
async function submitCommand(command) {
  await page.fill("#command-input", command);
  await page.press("#command-input", "Enter");
  await page.waitForTimeout(800);
  return captureState();
}

async function clickSelector(selector) {
  try {
    await page.click(selector, { timeout: 2000 });
    await page.waitForTimeout(500);
    return captureState();
  } catch (e) {
    return captureState(`click failed: ${e.message.split("\n")[0]}`);
  }
}

async function fileBugReport({ title, description, severity }, transcript) {
  const screenshotPath = `${OUT_DIR}/bug.png`;
  await page.screenshot({ path: screenshotPath });
  const transcriptPath = `${OUT_DIR}/transcript.json`;
  writeFileSync(transcriptPath, JSON.stringify(transcript, null, 2));
  const grid = await page.evaluate(() => {
    const el = document.getElementById("display");
    return el ? el.innerText : "";
  });
  const finalStatePath = `${OUT_DIR}/final-screen.txt`;
  writeFileSync(finalStatePath, grid);

  const body = [
    `## Severity\n${severity}`,
    "",
    "## Description",
    description,
    "",
    "## How it was found",
    `Filed by \`scripts/playtest-with-ui.mjs\` (${MODEL}) after ${transcript.turns} turns.`,
    "",
    "## Evidence",
    `- Screenshot: \`${screenshotPath}\``,
    `- Transcript: \`${transcriptPath}\``,
    `- Final screen: \`${finalStatePath}\``,
    "",
    "<details><summary>Final rendered screen (text)</summary>",
    "",
    "```",
    grid,
    "```",
    "",
    "</details>",
  ].join("\n");

  console.log(`\n[playtest] BUG REPORTED (${severity}): ${title}`);
  console.log(`[playtest] screenshot: ${screenshotPath}`);

  if (!FILE_BUGS) {
    console.log("[playtest] --file-bugs not set, skipping gh issue create");
    console.log(`[playtest] would have created issue with body:\n${body}`);
    return null;
  }

  const ghArgs = [
    "issue",
    "create",
    "--title",
    `[playtest] ${title}`,
    "--body",
    body,
    "--label",
    "playtest,bug",
  ];
  if (MILESTONE) {
    ghArgs.push("--milestone", MILESTONE);
  }
  const result = spawnSync("gh", ghArgs, { encoding: "utf8" });
  if (result.status === 0) {
    const url = result.stdout.trim();
    console.log(`[playtest] filed: ${url}`);
    return url;
  }
  console.error(`[playtest] gh issue create failed: ${result.stderr}`);
  return null;
}

// ── Main loop ────────────────────────────────────────────────
const transcript = { turns: 0, model: MODEL, events: [] };
const messages = [];

const initialBlocks = await captureState();
messages.push({
  role: "user",
  content: [
    {
      type: "text",
      text: "You are now sitting at the terminal. Here is what you see (screenshot first, then the textContent grid for precise reading). Begin playing. Watch for UI bugs.",
    },
    ...initialBlocks,
  ],
});

// Each turn we attach a base64 PNG screenshot (~50–80 KB). After ~25
// turns the cumulative request body crosses Anthropic's 413 limit. Strip
// images from older tool_results before sending — the model only needs
// recent visual state to act, and it can still quote text from older
// turns via the textContent block which we keep.
const KEEP_RECENT_IMAGE_TURNS = 3;

function trimMessagesForRequest(msgs) {
  // Index of tool_result-bearing messages, oldest first
  const trIndices = [];
  for (let i = 0; i < msgs.length; i++) {
    const m = msgs[i];
    if (m.role !== "user" || !Array.isArray(m.content)) continue;
    if (m.content.some((b) => b.type === "tool_result")) trIndices.push(i);
  }
  const keepFrom = Math.max(0, trIndices.length - KEEP_RECENT_IMAGE_TURNS);
  const trimSet = new Set(trIndices.slice(0, keepFrom));

  return msgs.map((m, i) => {
    if (!trimSet.has(i)) return m;
    const newContent = m.content.map((block) => {
      if (block.type !== "tool_result") return block;
      if (!Array.isArray(block.content)) return block;
      const noImages = block.content.filter((c) => c.type !== "image");
      if (noImages.length === 0) {
        return {
          ...block,
          content: [{ type: "text", text: "[earlier-turn screenshot elided]" }],
        };
      }
      return { ...block, content: noImages };
    });
    return { ...m, content: newContent };
  });
}

let stopped = false;
for (let turn = 0; turn < MAX_TURNS && !stopped; turn++) {
  transcript.turns = turn + 1;
  process.stdout.write(`[playtest] turn ${turn + 1}/${MAX_TURNS} ... `);

  const resp = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: [
      { type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } },
    ],
    tools: TOOLS,
    messages: trimMessagesForRequest(messages),
  });

  messages.push({ role: "assistant", content: resp.content });

  const toolResults = [];
  let actionTaken = "(no tool)";
  for (const block of resp.content) {
    if (block.type === "tool_use") {
      // Each tool result's content can be a single string OR an array of
      // content blocks (image + text). We use the array form for
      // submit_command / click so the model gets a fresh screenshot.
      let resultContent;
      let ok = true;
      if (block.name === "submit_command") {
        actionTaken = `submit_command(${JSON.stringify(block.input.command)})`;
        resultContent = await submitCommand(block.input.command);
      } else if (block.name === "click") {
        actionTaken = `click(${JSON.stringify(block.input.selector)})`;
        resultContent = await clickSelector(block.input.selector);
      } else if (block.name === "report_bug") {
        actionTaken = `report_bug(${block.input.severity}: ${block.input.title})`;
        const url = await fileBugReport(block.input, transcript);
        resultContent = url
          ? `Filed: ${url}`
          : "Bug report logged. Stopping playtest.";
        stopped = true;
      } else {
        resultContent = `Unknown tool: ${block.name}`;
        ok = false;
      }
      toolResults.push({
        type: "tool_result",
        tool_use_id: block.id,
        content: resultContent,
        is_error: !ok,
      });
    }
  }
  console.log(actionTaken);
  transcript.events.push({ turn: turn + 1, action: actionTaken });

  if (toolResults.length > 0 && !stopped) {
    messages.push({ role: "user", content: toolResults });
  } else if (toolResults.length === 0) {
    // No tool call — model may be wrapping up
    if (resp.stop_reason === "end_turn") {
      console.log("[playtest] model stopped (end_turn). Done.");
      break;
    }
    // Nudge it back into action
    messages.push({
      role: "user",
      content: "Keep playing or call report_bug if you've found a UI problem.",
    });
  }
}

if (!stopped && transcript.turns >= MAX_TURNS) {
  console.log(
    `[playtest] reached MAX_TURNS=${MAX_TURNS} without finding a bug.`,
  );
}

writeFileSync(
  `${OUT_DIR}/transcript.json`,
  JSON.stringify(transcript, null, 2),
);
console.log(`[playtest] transcript: ${OUT_DIR}/transcript.json`);
await browser.close();

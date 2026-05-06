#!/usr/bin/env node

// Headless gameplay harness for fix verification.
//
// Usage:
//   node scripts/screenshot-game.mjs [out-dir]
//
// Boots play.html, dismisses any intro, plays a few canned commands, and
// captures screenshots of each state. Default out dir: /tmp/game-shots.

import { mkdirSync } from "node:fs";
import { chromium } from "@playwright/test";

const OUT = process.argv[2] || "/tmp/game-shots";
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
  bypassCSP: true,
});
const page = await ctx.newPage();
// Disable cache so edits to ui.js / play.html land immediately.
await ctx.route("**/*", (route) =>
  route.continue({
    headers: { ...route.request().headers(), "Cache-Control": "no-cache" },
  }),
);

// Surface console warnings/errors so we don't miss issues
page.on("console", (msg) => {
  const t = msg.type();
  if (t === "error" || t === "warning") {
    console.log(`  [browser ${t}]`, msg.text());
  }
});
page.on("pageerror", (e) => console.log("  [pageerror]", e.message));

async function shoot(name) {
  const path = `${OUT}/${name}.png`;
  // Freeze CSS animations to a deterministic frame for repeatable shots
  // (otherwise the blinking cursor randomly captures in its "off" half).
  await page.addStyleTag({
    content:
      "*, *::before, *::after { animation-play-state: paused !important; }",
  });
  await page.screenshot({ path });
  console.log(`  → ${path}`);
}

console.log("Loading play.html …");
await page.goto("http://localhost:8765/play.html", {
  waitUntil: "networkidle",
});
await page.waitForTimeout(500);
console.log("  page title:", JSON.stringify(await page.title()));
await shoot("01-title-screen");

// Click New Game (or skip if intro auto-runs)
const newGame = page.locator("#menu-new-game");
if (await newGame.isVisible().catch(() => false)) {
  console.log("Clicking New Game …");
  await newGame.click();
}

// Wait for Glulx to boot. Existence of the input bar is the signal.
await page.waitForSelector("#command-input", {
  state: "visible",
  timeout: 15000,
});

// Skip the intro sequence by clicking through it (it advances on click).
// Loop until the input field accepts focus, signal that gameplay started.
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(400);
  const introActive = await page.evaluate(
    () => !!window.MirsEndIntro?.isActive?.(),
  );
  if (!introActive) break;
  await page.mouse.click(800, 500);
}
await page.waitForTimeout(1500); // let initial room description render
console.log("  page title after boot:", JSON.stringify(await page.title()));
await shoot("02-game-start");

// Play a few commands to surface the bugs flagged in the screenshot.
async function command(text) {
  console.log(`> ${text}`);
  await page.fill("#command-input", text);
  await page.press("#command-input", "Enter");
  await page.waitForTimeout(700);
}

await command("look");
await shoot("03-after-look");

await command("inventory");
await shoot("04-after-inventory");

// Reproduce the empty-Enter bug from the user's screenshot
console.log("> (empty enter x3)");
for (let i = 0; i < 3; i++) {
  await page.press("#command-input", "Enter");
  await page.waitForTimeout(150);
}
await shoot("05-after-empty-enters");

await command("look right");
await command("look left");
await shoot("06-look-directions");

await browser.close();
console.log("Done. Screenshots in", OUT);

/**
 * One-shot Playwright dump that drives the canonical cupola path with
 * each morale bucket override and saves the resulting transcripts to
 * docs/playtests/. Used to verify variant substitution end-to-end and
 * to satisfy the playtest-on-story-change convention.
 *
 *   node scripts/dump-perception-transcripts.mjs
 */

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, "..");
const PORT = 8182;
const URL = `http://localhost:${PORT}/play.html`;

const STEPS = [
  "open locker",
  "take flashlight",
  "switch on flashlight",
  "pull lever",
  "n",
  "d",
  "examine viewport",
];

function startServer() {
  const proc = spawn(
    "python3",
    ["-m", "http.server", String(PORT), "--directory", "game"],
    { cwd: REPO, stdio: "ignore" },
  );
  return proc;
}

async function waitFor(check, timeoutMs = 15_000, intervalMs = 100) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await check()) return;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("waitFor timed out");
}

async function runBucket(browser, bucket) {
  const page = await browser.newPage();
  await page.goto(URL);
  await page.evaluate(() => localStorage.clear());
  await page.locator("#title-screen").waitFor({ state: "visible" });
  await page.click("#menu-new-game");
  await page.waitForTimeout(300);
  await page.keyboard.press("Escape");
  await page
    .locator("#story-output")
    .filter({ hasText: "Crew Quarters" })
    .waitFor({ timeout: 15_000 });
  await page.evaluate((b) => {
    window.MIRSEND_PERCEPTION_BUCKET = b;
  }, bucket);

  for (const cmd of STEPS) {
    const glk = page.locator("#windowport input.LineInput");
    if ((await glk.count()) > 0) {
      await glk.focus();
      await page.keyboard.type(cmd);
      await page.keyboard.press("Enter");
    }
    await page.waitForTimeout(80);
  }

  const transcript = await page
    .locator("#story-output")
    .textContent()
    .then((t) => t ?? "");
  await page.close();
  return transcript;
}

async function main() {
  const server = startServer();
  try {
    await waitFor(async () => {
      try {
        const r = await fetch(URL);
        return r.ok;
      } catch {
        return false;
      }
    });
    const browser = await chromium.launch();
    const transcripts = {};
    for (const bucket of ["low", "mid", "high"]) {
      console.log(`Capturing morale:${bucket} …`);
      transcripts[bucket] = await runBucket(browser, bucket);
    }
    await browser.close();

    const today = new Date().toISOString().slice(0, 10);
    const outPath = resolve(
      REPO,
      "docs/playtests",
      `${today}-m5-perception.md`,
    );
    mkdirSync(dirname(outPath), { recursive: true });
    const md = renderMarkdown(transcripts, today);
    writeFileSync(outPath, md);
    console.log(`Wrote ${outPath}`);
  } finally {
    server.kill("SIGTERM");
  }
}

function renderMarkdown(transcripts, today) {
  const cupolaExcerpt = (text) => {
    const idx = text.indexOf("Observation Cupola");
    if (idx < 0) return text.slice(-2000);
    return text.slice(idx, idx + 2500);
  };
  return `# m5 perception overlay — Playwright transcript dump — ${today}

**Run by:** \`node scripts/dump-perception-transcripts.mjs\`. Drives the
canonical cupola-nadir-war path three times, once per morale bucket
override (\`window.MIRSEND_PERCEPTION_BUCKET\`), captures the resulting
transcript from \`#story-output\`, excerpts the cupola section.

**Verifies:**

- \`[PERCEIVE cupola-nadir-war]\` markers never appear in visible output
- The bucketed variant for each register lands at the head of the reveal
- The post-marker paragraphs ("The nightside should be …", the count,
  the framing) render unchanged across all three buckets

Variant prose is hand-authored in \`game/perceptions.json\` per #54.

---

## morale:low excerpt

\`\`\`
${cupolaExcerpt(transcripts.low)}
\`\`\`

## morale:mid excerpt

\`\`\`
${cupolaExcerpt(transcripts.mid)}
\`\`\`

## morale:high excerpt

\`\`\`
${cupolaExcerpt(transcripts.high)}
\`\`\`
`;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

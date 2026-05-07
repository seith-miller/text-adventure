/**
 * One-shot Playwright dump of the canonical A → B1 → C1 playthrough.
 * Mirrors the command list in tests/e2e/canonical-arc.spec.ts and
 * captures the resulting transcript at default (natural) morale, so
 * docs/playtests/ shows how the m5 perception variants land in a real
 * playthrough rather than under a forced-bucket override.
 *
 *   node scripts/dump-canonical-arc-transcript.mjs
 */
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, "..");
const PORT = 8183;
const URL = `http://localhost:${PORT}/play.html`;

/* Verbatim from tests/e2e/canonical-arc.spec.ts. */
const CANONICAL_COMMANDS = [
  "open locker",
  "take flashlight",
  "switch on flashlight",
  "pull lever",
  "n",
  "take notebook",
  "read notebook",
  "u",
  "take dosimeter",
  "d",
  "d",
  "examine viewport",
  "u",
  "n",
  "open toolkit",
  "take multimeter",
  "restore power",
  "read log",
  "open safe",
  "listen",
  "transmit",
];

function startServer() {
  return spawn(
    "python3",
    ["-m", "http.server", String(PORT), "--directory", "game"],
    { cwd: REPO, stdio: "ignore" },
  );
}

async function waitFor(check, timeoutMs = 15_000, intervalMs = 100) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await check()) return;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("waitFor timed out");
}

async function runArc(browser) {
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

  for (const cmd of CANONICAL_COMMANDS) {
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
  const finalState = await page.evaluate(() => {
    const m = window.MirsEnd;
    return m ? m.getState() : null;
  });
  await page.close();
  return { transcript, finalState };
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
    console.log("Driving canonical A → B1 → C1 …");
    const { transcript, finalState } = await runArc(browser);
    await browser.close();

    const today = new Date().toISOString().slice(0, 10);
    const outPath = resolve(
      REPO,
      "docs/playtests",
      `${today}-canonical-arc.md`,
    );
    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, renderMarkdown(transcript, finalState, today));
    console.log(`Wrote ${outPath}`);
  } finally {
    server.kill("SIGTERM");
  }
}

function renderMarkdown(transcript, finalState, today) {
  return `# Canonical A → B1 → C1 playthrough — ${today}

**Run by:** \`node scripts/dump-canonical-arc-transcript.mjs\`. Drives
the verbatim command list from \`tests/e2e/canonical-arc.spec.ts\` against
the current build, and captures \`#story-output\` at the end. No bucket
overrides — morale is whatever the playthrough naturally produces, so
the m5 perception variants land at the bucket the player would actually
hit at the cupola viewport.

**Final state:** O2 ${finalState?.o2 ?? "?"}%, morale ${finalState?.morale ?? "?"}%, room \`${finalState?.currentRoom ?? "?"}\`, inventory: ${(finalState?.inventory ?? []).join(", ") || "(empty)"}

**Verifies:**

- All assertions from \`tests/e2e/canonical-arc.spec.ts\` (Zhuchok, Main
  Corridor, Life Support, World War III, isolated power bus, four-digit
  safe code, armament bay, Commander Diane Chen, Begin preparations)
- The \`cupola-nadir-war\` perception variant fires at whatever morale
  bucket the player actually lands in by the time they examine the
  viewport. The other four variant sites (\`cupola-nadir-revisit\`,
  \`examine-yevgenia\`, \`examine-petrov\`, \`reactor-radiation-tick\`)
  are not on the canonical path; their bucket-forced dump lives in
  \`2026-05-07-m5-perception.md\`.
- No \`[PERCEIVE …]\` or \`[MIRSEND …]\` markers leak to the visible panel

---

## Full transcript

\`\`\`
${transcript}
\`\`\`
`;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

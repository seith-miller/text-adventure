import { chromium } from "@playwright/test";

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
});
const page = await ctx.newPage();

const targets = [
  {
    url: "http://localhost:8765/mockups/v3-textmode.html",
    out: "docs/ui-mockups/v3-textmode.png",
  },
  {
    url: "http://localhost:8765/mockups/v4-video.html",
    out: "docs/ui-mockups/v4-video.png",
  },
  {
    url: "http://localhost:8765/mockups/v5-cutscene.html",
    out: "docs/ui-mockups/v5-cutscene.png",
  },
];
for (const t of targets) {
  await page.goto(t.url, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: t.out, fullPage: false });
  console.log("wrote", t.out);
}
await browser.close();

/**
 * Catalog test — enforces that every feature listed in features.yaml
 * has a matching <id>.spec.ts file. Prevents silent drift between
 * "what we promise" and "what we test".
 */

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";

interface FeatureEntry {
  id: string;
  area: string;
  demonstrates: string;
  surfaces?: string[];
}

/** Tiny YAML reader — avoids adding a dep for the few fields we use. */
function parseFeatures(path: string): FeatureEntry[] {
  const text = readFileSync(path, "utf-8");
  const entries: FeatureEntry[] = [];
  let current: Partial<FeatureEntry> | null = null;
  let pendingKey: string | null = null;
  let foldedLines: string[] = [];

  const flushFolded = () => {
    if (pendingKey && current) {
      (current as any)[pendingKey] = foldedLines.join(" ").trim();
    }
    pendingKey = null;
    foldedLines = [];
  };

  for (const raw of text.split("\n")) {
    if (raw.startsWith("#") || raw.trim() === "") {
      flushFolded();
      continue;
    }
    if (raw.startsWith("- id:")) {
      flushFolded();
      if (current?.id) entries.push(current as FeatureEntry);
      current = { id: raw.split(":")[1].trim() };
    } else if (raw.startsWith("  ") && current) {
      const line = raw.trim();
      const colonIdx = line.indexOf(":");
      if (colonIdx > 0 && !pendingKey) {
        const key = line.slice(0, colonIdx).trim();
        const val = line.slice(colonIdx + 1).trim();
        if (val === ">") {
          pendingKey = key;
        } else if (val.startsWith("[") && val.endsWith("]")) {
          (current as any)[key] = val
            .slice(1, -1)
            .split(",")
            .map((s) => s.trim());
        } else {
          (current as any)[key] = val;
        }
      } else if (pendingKey) {
        foldedLines.push(line);
      }
    }
  }
  flushFolded();
  if (current?.id) entries.push(current as FeatureEntry);
  return entries;
}

test("every feature in features.yaml has a matching spec file", () => {
  const features = parseFeatures(join(__dirname, "features.yaml"));
  expect(features.length).toBeGreaterThan(0);

  const missing: string[] = [];
  for (const f of features) {
    const spec = join(__dirname, `${f.id}.spec.ts`);
    if (!existsSync(spec)) missing.push(f.id);
  }
  expect(missing, `Missing spec files: ${missing.join(", ")}`).toEqual([]);
});

test("every feature declares area + demonstrates", () => {
  const features = parseFeatures(join(__dirname, "features.yaml"));
  for (const f of features) {
    expect(f.area, `${f.id} missing area`).toBeTruthy();
    expect(f.demonstrates, `${f.id} missing demonstrates`).toBeTruthy();
  }
});

/**
 * Compile .ink files to JSON using inkjs's built-in Compiler.
 *
 * Rationale: Using inkjs's built-in compiler avoids a native dependency on
 * inklecate (which requires Mono/.NET) and keeps the toolchain pure Node.js.
 * This makes setup simpler and more portable across platforms.
 */

import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import { Compiler } from "inkjs/compiler/Compiler";

const storyDir = join("game", "story");
const outDir = join("game", "dist", "story");

mkdirSync(outDir, { recursive: true });

const inkFiles = readdirSync(storyDir).filter((f) => f.endsWith(".ink"));

if (inkFiles.length === 0) {
  console.log("No .ink files found in game/story/");
  process.exit(0);
}

let hasError = false;

for (const file of inkFiles) {
  const inputPath = join(storyDir, file);
  const outputName = `${basename(file, ".ink")}.json`;
  const outputPath = join(outDir, outputName);

  console.log(`Compiling ${inputPath} -> ${outputPath}`);

  try {
    const source = readFileSync(inputPath, "utf-8");
    const compiler = new Compiler(source);
    const story = compiler.Compile();
    const json = story.ToJson();
    writeFileSync(outputPath, json);
  } catch (err) {
    console.error(`Error compiling ${file}:`, err.message);
    hasError = true;
  }
}

if (hasError) {
  process.exit(1);
}

console.log(`Compiled ${inkFiles.length} ink file(s) successfully.`);

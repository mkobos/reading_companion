#!/usr/bin/env node
// Security assertion (Phase 1 plan §6.1): no `dangerouslySetInnerHTML`
// anywhere in the frontend source. This script is wired into `npm run
// lint` as a hard gate, in addition to grep-based CI/manual checks.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(import.meta.dirname, "..", "src");
const FORBIDDEN = "dangerouslySetInnerHTML";

/** @param {string} dir */
function walk(dir) {
  /** @type {string[]} */
  const matches = [];
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) {
      matches.push(...walk(path));
    } else if (readFileSync(path, "utf8").includes(FORBIDDEN)) {
      matches.push(path);
    }
  }
  return matches;
}

const matches = walk(ROOT);
if (matches.length > 0) {
  console.error(`Forbidden "${FORBIDDEN}" found in:\n${matches.join("\n")}`);
  process.exit(1);
}
console.log(`OK: no "${FORBIDDEN}" usage in src/`);

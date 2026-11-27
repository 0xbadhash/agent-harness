#!/usr/bin/env node
// Fail when an ESLint rule count rises above the recorded floor.
import { readFileSync } from "node:fs";

const [, , reportPath, baselinePath] = process.argv;
if (!reportPath || !baselinePath) {
  console.error("usage: eslint-ratchet.mjs <eslint-report.json> <baseline.json>");
  process.exit(2);
}

const report = JSON.parse(readFileSync(reportPath, "utf8"));
const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
const counts = {};
for (const file of report) {
  for (const message of file.messages ?? []) {
    counts[message.ruleId] = (counts[message.ruleId] ?? 0) + 1;
  }
}

let failed = false;
for (const [rule, count] of Object.entries(counts)) {
  const floor = baseline[rule] ?? 0;
  if (count > floor) {
    console.error(`${rule}: ${count} violations (floor ${floor})`);
    failed = true;
  }
}
console.log(failed ? "ratchet failed" : "ratchet ok");
process.exit(failed ? 1 : 0);

# ESLint ratchet template

Copy this directory into a product repo that ships JavaScript or TypeScript.

- `eslint.config.mjs` — the shared ruleset, including the anti-patterns the
  harness rejects (floating promises, `any` escapes, silent catches, and
  `console` in library code).
- `baseline.json` — the current violation count per rule. CI fails when a count
  rises above the floor.

Run in CI:

```bash
npx eslint . --format json --output-file eslint-report.json
node scripts/eslint-ratchet.mjs eslint-report.json baseline.json
```

Raise the floor only after the count falls, and say why in the commit. The
ratchet makes a large product adopt the rules without a flag day.

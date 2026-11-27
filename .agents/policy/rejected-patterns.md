# Rejected patterns

Docs and skills must not teach these. The checker allows a line that names the
pattern as retired, removed, forbidden, or replaced.

| Pattern | Why it is rejected | Use instead |
|---------|--------------------|-------------|
| `--yolo` | skips every gate | the phase FSM and its gates |
| `--no-interview` / `--no-clarify` | retires the grill and the clarify pass | `--spike` with a recorded reason |
| `git push origin main` | `main` is protected; direct pushes fail | branch + PR + squash merge |
| bare `# type: ignore` | hides new type errors | a specific code or a real fix |
| `print()` in library code | bypasses the log/telemetry path | the logger or the artifact writer |

`python3 scripts/check_docs_patterns.py --root .` scans `docs/`, `skills/`,
`templates/`, `README.md`, and `AGENTS.md`. Historical specs under `docs/specs/`
are excluded. A line that explains why the pattern is rejected passes.

#!/usr/bin/env python3
"""Create a task worksheet under .agents/traces/ (agentic harness — not product UI).

Usage:
  python3 scripts/generate_worksheet.py --task-id orch-p1p2 --title "Harness P1-P2"
  python3 scripts/generate_worksheet.py --task-id x --title "Y" --out-dir /tmp/traces
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / ".agents" / "traces"

SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,80}$")

TEMPLATE = """# Worksheet: {title}

```yaml
task-id: {task_id}
created: {created}
status: open
```

## Goals
- {title}

## Steps
1. Research / load AGENTS.md + GEMINI.md routing
2. Plan verifiable acceptance
3. Implement (TDD) + **run the app** where applicable
4. Validate (`scripts/validate.py full` / skill gates)
5. Self-heal docs / vault log if product change

## Decisions
- (none yet)

## Issues
- (none yet)

## Learnings
- (none yet)

## §9 things_that_look_bad_but_are_fine
```yaml
things_that_look_bad_but_are_fine: []
```
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate traces/<task-id>.md worksheet")
    p.add_argument("--task-id", required=True, help="Slug used as filename")
    p.add_argument("--title", required=True, help="Human title")
    p.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory (default: repo traces/)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing worksheet",
    )
    args = p.parse_args(argv)

    task_id = args.task_id.strip()
    if not SAFE_ID.match(task_id):
        print(f"❌ invalid task-id: {task_id!r} (use alnum, ._- )", file=sys.stderr)
        return 2

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{task_id}.md"

    if path.exists() and not args.force:
        print(f"⏭️  SKIP exists: {path}")
        return 0

    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = TEMPLATE.format(
        title=args.title.strip(),
        task_id=task_id,
        created=created,
    )
    path.write_text(body, encoding="utf-8")
    print(f"✅ worksheet: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Write .agents/artifacts/CONTEXT_PACK.md for ship start (B3)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def build_pack(root: Path) -> str:
    root = Path(root).resolve()
    lines = [
        "# CONTEXT_PACK",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Root:** `{root}`",
        "",
        "## Constitution / constraints",
        "",
    ]
    for rel in (
        ".agents/CONSTITUTION.md",
        "AGENTS.md",
        ".agents/policy/base_constraints.md",
    ):
        p = root / rel
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            snippet = "\n".join(text.splitlines()[:40])
            lines.append(f"### {rel}")
            lines.append("")
            lines.append("```")
            lines.append(snippet)
            lines.append("```")
            lines.append("")
            break
    else:
        lines.append("_No constitution/AGENTS found — use policy defaults._")
        lines.append("")

    lines.extend(
        [
            "## Open risks / decisions",
            "",
            "- (fill during /execute_dev)",
            "",
            "## Plugin smoke",
            "",
        ]
    )
    plugin = root / ".agents" / "product_plugin.yaml"
    if plugin.is_file():
        lines.append("```yaml")
        lines.append("\n".join(plugin.read_text(encoding="utf-8").splitlines()[:60]))
        lines.append("```")
    else:
        lines.append("_No product_plugin.yaml_")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Default: <root>/.agents/artifacts/CONTEXT_PACK.md",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()
    out = args.out or (root / ".agents" / "artifacts" / "CONTEXT_PACK.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = build_pack(root)
    out.write_text(text, encoding="utf-8")
    print(f"✅ wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

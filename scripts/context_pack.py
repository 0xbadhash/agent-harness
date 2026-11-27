#!/usr/bin/env python3
"""Write .agents/artifacts/CONTEXT_PACK.md for ship start (B3)."""
from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path

PROTOTYPE_RE = re.compile(r"\*\*Prototype verdict:\*\*\s*(.+)", re.IGNORECASE)
RESERVED_RE = re.compile(r"\*\*Reserved decisions:\*\*\s*(.+)", re.IGNORECASE)
DELEGATED_RE = re.compile(r"\*\*Delegated decisions:\*\*\s*(.+)", re.IGNORECASE)
ADR_RE = re.compile(r"\bADR[-\s](\d{3})\b")
QA_RE = re.compile(r"^\s*[-*]?\s*Q:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def _section(text: str, header: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(header)}\b(.*?)(?=^##\s|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def _spec_text(root: Path, spec: Path | None) -> str:
    if spec is not None and spec.is_file():
        return spec.read_text(encoding="utf-8", errors="replace")
    pipeline = root / ".agents" / "state" / "pipeline.json"
    if pipeline.is_file():
        import json

        try:
            data = json.loads(pipeline.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        rel = str(data.get("spec_id") or "")
        candidate = root / rel if rel else None
        if candidate and candidate.is_file():
            return candidate.read_text(encoding="utf-8", errors="replace")
    return ""


def build_grill_handoff(root: Path, spec: Path | None = None) -> str:
    """Compact the grill into the artifact a fresh session can resume from."""
    root = Path(root).resolve()
    text = _spec_text(root, spec)
    grill = _section(text, "Grill-me")
    questions = [q.strip() for q in QA_RE.findall(grill)]
    lines = [
        "# GRILL_HANDOFF",
        "",
        f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "## Decisions settled in the grill",
        "",
    ]
    if questions:
        lines.extend(f"- {q}" for q in questions[:12])
    else:
        lines.append("- none recorded — resume the grill before AFK work")

    lines.extend(["", "## Decision ownership", ""])
    for label, rx in (("Reserved", RESERVED_RE), ("Delegated", DELEGATED_RE)):
        match = rx.search(text)
        lines.append(f"- **{label}:** {match.group(1).strip() if match else 'not recorded'}")
    lines.extend(
        [
            "",
            "## Glossary changes",
            "",
            "- none recorded" if "glossary" not in text.lower() else "- see GLOSSARY.md diff in the spec",
            "",
            "## ADR links",
            "",
        ]
    )
    adrs = sorted(set(ADR_RE.findall(text)))
    if adrs:
        lines.extend(f"- ADR {n}" for n in adrs)
    else:
        lines.append("- none")
    lines.extend(["", "## Prototype", ""])
    proto = PROTOTYPE_RE.search(text)
    lines.append(f"- **Verdict:** {proto.group(1).strip() if proto else 'not-applicable'}")
    open_q = _section(text, "Open questions").strip()
    lines.extend(
        [
            "",
            "## Open questions",
            "",
            open_q if open_q and "none" not in open_q.lower() else "- none",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(root: Path) -> str:
    root = Path(root).resolve()
    lines = [
        "# CONTEXT_PACK",
        "",
        f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
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
    ap.add_argument(
        "--compact",
        action="store_true",
        help="Write the grill handoff instead of the full pack",
    )
    ap.add_argument("--spec", type=Path, default=None, help="Spec to compact")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if args.compact:
        out = args.out or (root / ".agents" / "artifacts" / "GRILL_HANDOFF.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        spec = args.spec
        if spec is not None and not spec.is_absolute():
            spec = root / spec
        out.write_text(build_grill_handoff(root, spec), encoding="utf-8")
        print(f"✅ wrote {out}")
        return 0
    out = args.out or (root / ".agents" / "artifacts" / "CONTEXT_PACK.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = build_pack(root)
    out.write_text(text, encoding="utf-8")
    print(f"✅ wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

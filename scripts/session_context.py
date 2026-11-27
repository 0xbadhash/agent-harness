#!/usr/bin/env python3
"""P2 Organize pack — one-shot session context for operators and LLMs.

Prints (and optionally writes) a compact pack:
  phase, OPEN roadmap, night FAIL products, harness lag, push hints.

  python3 scripts/session_context.py
  python3 scripts/session_context.py --root . --write
  python3 scripts/session_context.py --json

Does not change pipeline phase. CODER mode: primarily Organize (+ Display).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
SCRIPTS = HARNESS / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@dataclass
class SessionContext:
    generated_at: str
    root: str
    phase: str
    score: float | None
    task: str | None
    open_roadmap: list[str] = field(default_factory=list)
    night_fail_products: list[str] = field(default_factory=list)
    harness_sot_version: str | None = None
    harness_product_version: str | None = None
    portfolio_lagging: list[str] = field(default_factory=list)
    git_branch: str | None = None
    git_dirty: bool = False
    remote_sync: str | None = None
    next_hints: list[str] = field(default_factory=list)
    coders: list[str] = field(default_factory=list)
    tokens: str = "unknown"
    context_tokens: str = "unknown"
    cost_usd: str = "unknown"
    cost_source: str = "not-recorded"


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _open_roadmap(root: Path) -> list[str]:
    roadmap = root / "CHANGELOG.md"
    plugin = root / ".agents" / "product_plugin.yaml"
    if plugin.is_file():
        for ln in plugin.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.strip().startswith("product_roadmap:"):
                cand = root / ln.split(":", 1)[1].strip()
                if cand.is_file():
                    roadmap = cand
                break
    if not roadmap.is_file():
        return []
    return [
        m.group(1).strip()
        for m in re.finditer(
            r"^### \[OPEN\]\s*(.+)$",
            roadmap.read_text(encoding="utf-8", errors="replace"),
            re.MULTILINE,
        )
    ]


def _night_fails(root: Path) -> list[str]:
    fails: list[str] = []
    mt = root / ".agents" / "artifacts" / "MORNING_TRIAGE.md"
    # Prefer harness SoT morning triage when scanning from a product
    candidates = [mt, HARNESS / ".agents" / "artifacts" / "MORNING_TRIAGE.md"]
    for p in candidates:
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "**FAIL**" in line or "| **FAIL**" in line:
                m = re.search(r"`([a-zA-Z0-9_-]+)`", line)
                if m and m.group(1) not in fails:
                    fails.append(m.group(1))
        if fails:
            break
    return fails


def _portfolio_lag() -> tuple[str | None, list[str]]:
    sot = None
    ver = HARNESS / "VERSION"
    if ver.is_file():
        sot = ver.read_text(encoding="utf-8").strip()
    lagging: list[str] = []
    products = HARNESS / "config" / "night_shift_products.yaml"
    if not products.is_file() or not sot:
        return sot, lagging
    for line in products.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, raw = line.split(":", 1)
        pid = pid.strip()
        if pid == "agent-harness":
            continue
        root = Path(os.path.expanduser(raw.strip())).resolve()
        hv = root / ".agents" / "HARNESS_VERSION"
        if not hv.is_file():
            lagging.append(f"{pid}:missing")
            continue
        v = hv.read_text(encoding="utf-8").lstrip("\ufeff").strip()
        if v != sot:
            lagging.append(f"{pid}:{v}")
    return sot, lagging


def _session_cost(root: Path) -> dict[str, str]:
    """Read recorded token/cost evidence; never invent a number."""
    path = root / ".agents" / "artifacts" / "session_cost.json"
    data = _read_json(path)
    source = str(path.name) if data else "not-recorded"
    tokens = data.get("tokens") or os.environ.get("SESSION_TOKENS") or "unknown"
    context = data.get("context_tokens") or os.environ.get("SESSION_CONTEXT_TOKENS") or "unknown"
    cost = data.get("cost_usd") or os.environ.get("SESSION_COST_USD") or "unknown"
    if source == "not-recorded" and (tokens != "unknown" or cost != "unknown"):
        source = "environment"
    return {
        "tokens": str(tokens),
        "context_tokens": str(context),
        "cost_usd": str(cost),
        "source": source,
    }


def _git(root: Path) -> tuple[str | None, bool, str | None]:
    def run(args: list[str]) -> tuple[int, str]:
        r = subprocess.run(
            args, cwd=str(root), capture_output=True, text=True, check=False
        )
        return r.returncode, (r.stdout or "").strip()

    rc, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        return None, False, None
    rc, porc = run(["git", "status", "--porcelain"])
    dirty = bool(porc)
    rc, sb = run(["git", "status", "-sb"])
    remote = "unknown"
    if rc == 0 and sb:
        line = sb.splitlines()[0]
        if "ahead" in line and "behind" in line:
            remote = "diverged"
        elif "ahead" in line:
            remote = "ahead"
        elif "behind" in line:
            remote = "behind"
        elif "..." in line or "origin" in line:
            remote = "ok"
        else:
            remote = "no_upstream"
    return branch, dirty, remote


def build(root: Path) -> SessionContext:
    root = root.resolve()
    pipe = _read_json(root / ".agents" / "state" / "pipeline.json")
    phase = str(pipe.get("phase") or "unknown")
    score = pipe.get("score")
    try:
        score_f = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_f = None
    sot, lag = _portfolio_lag()
    prod_ver = None
    hv = root / ".agents" / "HARNESS_VERSION"
    if hv.is_file():
        prod_ver = hv.read_text(encoding="utf-8").lstrip("\ufeff").strip()
    elif (root / "VERSION").is_file():
        prod_ver = (root / "VERSION").read_text(encoding="utf-8").strip()
    branch, dirty, remote = _git(root)
    opens = _open_roadmap(root)
    fails = _night_fails(root)
    cost = _session_cost(root)

    hints: list[str] = []
    if phase in ("init", "blocked"):
        hints.append("If feature work: /spec (or waiver) then /execute_dev")
    if phase == "ready_for_review":
        hints.append("NEXT: /pr_review --validate")
    if phase == "approved":
        hints.append("NEXT: /release_mgmt (infra verify only if required)")
    if phase == "shipped":
        hints.append("NEXT: /sync_docs → init")
    if fails:
        hints.append(
            f"Night FAIL products: {', '.join(fails)} — "
            "morning_triage / night_fail_remediate / product fix"
        )
    if lag:
        hints.append(
            "Portfolio lag — python3 scripts/portfolio_install_report.py --install --push"
        )
    if dirty:
        hints.append("Working tree dirty — commit/stash before push proof")
    if remote == "ahead":
        hints.append("Local ahead of origin — git push")

    return SessionContext(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        root=str(root),
        phase=phase,
        score=score_f,
        task=pipe.get("task"),
        open_roadmap=opens,
        night_fail_products=fails,
        harness_sot_version=sot,
        harness_product_version=prod_ver,
        portfolio_lagging=lag,
        git_branch=branch,
        git_dirty=dirty,
        remote_sync=remote,
        next_hints=hints,
        coders=["Organize", "Display", "Compute"],
        tokens=cost["tokens"],
        context_tokens=cost["context_tokens"],
        cost_usd=cost["cost_usd"],
        cost_source=cost["source"],
    )


def to_markdown(ctx: SessionContext) -> str:
    lines = [
        "# SESSION_CONTEXT",
        "",
        f"_Generated {ctx.generated_at} by session_context.py_",
        "",
        f"**CODER modes:** {', '.join(ctx.coders)} (Organize pack — not a new FSM)",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| root | `{ctx.root}` |",
        f"| phase | `{ctx.phase}` |",
        f"| score | `{ctx.score}` |",
        f"| task | {ctx.task or '—'} |",
        f"| branch | `{ctx.git_branch}` |",
        f"| dirty | `{ctx.git_dirty}` |",
        f"| remote | `{ctx.remote_sync}` |",
        f"| harness SoT | `{ctx.harness_sot_version}` |",
        f"| this tree harness | `{ctx.harness_product_version}` |",
        f"| tokens | `{ctx.tokens}` |",
        f"| context tokens | `{ctx.context_tokens}` |",
        f"| cost (USD) | `{ctx.cost_usd}` |",
        f"| cost source | `{ctx.cost_source}` |",
        "",
        "## Open roadmap",
        "",
    ]
    if ctx.open_roadmap:
        for o in ctx.open_roadmap:
            lines.append(f"- [ ] {o}")
    else:
        lines.append("- (none `[OPEN]`)")
    lines.extend(["", "## Night FAIL products", ""])
    if ctx.night_fail_products:
        for p in ctx.night_fail_products:
            lines.append(f"- `{p}`")
    else:
        lines.append("- (none detected in MORNING_TRIAGE)")
    lines.extend(["", "## Portfolio lag", ""])
    if ctx.portfolio_lagging:
        for p in ctx.portfolio_lagging:
            lines.append(f"- {p}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Hints", ""])
    for h in ctx.next_hints or ["—"]:
        lines.append(f"- {h}")
    lines.extend(
        [
            "",
            "## Refresh",
            "",
            "```bash",
            "python3 scripts/session_context.py --write",
            "python3 scripts/remaining_board.py",
            "python3 scripts/night_shift_morning_triage.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--write", action="store_true", help="Write .agents/artifacts/SESSION_CONTEXT.md")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record-tokens", type=int, default=None)
    ap.add_argument("--record-context", type=int, default=None)
    ap.add_argument("--record-cost", type=float, default=None)
    args = ap.parse_args(argv)
    root = args.root.resolve()

    if any(
        value is not None
        for value in (args.record_tokens, args.record_context, args.record_cost)
    ):
        path = root / ".agents" / "artifacts" / "session_cost.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _read_json(path)
        if args.record_tokens is not None:
            data["tokens"] = args.record_tokens
        if args.record_context is not None:
            data["context_tokens"] = args.record_context
        if args.record_cost is not None:
            data["cost_usd"] = args.record_cost
        data["recorded_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"✅ recorded session cost → {path}")

    ctx = build(root)
    if args.json:
        print(json.dumps(asdict(ctx), indent=2))
    else:
        md = to_markdown(ctx)
        print(md)
        if args.write:
            out = root / ".agents" / "artifacts" / "SESSION_CONTEXT.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            print(f"wrote {out}", file=sys.stderr)
            cost_md = (
                "# SESSION_COST\n\n"
                f"_Generated {ctx.generated_at} by session_context.py_\n\n"
                "| Field | Value |\n|-------|-------|\n"
                f"| tokens | `{ctx.tokens}` |\n"
                f"| context tokens | `{ctx.context_tokens}` |\n"
                f"| cost (USD) | `{ctx.cost_usd}` |\n"
                f"| source | `{ctx.cost_source}` |\n\n"
                "Record with `python3 scripts/session_context.py --record-tokens N "
                "--record-context N --record-cost USD`. An `unknown` value means the "
                "session metadata was not available; it is never fabricated.\n"
            )
            cost_out = root / ".agents" / "artifacts" / "SESSION_COST.md"
            cost_out.write_text(cost_md, encoding="utf-8")
            print(f"wrote {cost_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

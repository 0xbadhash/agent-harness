#!/usr/bin/env python3
"""Weekly (or on-demand) root/containerd IoC scan for known npm malware seeds.

Detects ChainDrop / keyv-style campaign fingerprints under:
  - /home (product trees)
  - /opt
  - /var/lib/containerd (needs root/sudo)
  - optional extra roots via --root

Writes:
  $PRODUCT_VAULT_ROOT/agent-tasks/security-ioc-status.md
  $PRODUCT_VAULT_ROOT/agent-tasks/security-ioc-last.json

Behavior vs OPS-DASHBOARD:
  - Always updates security-ioc-status.md (audit trail).
  - On findings: marks JSON status=fail and runs ops_dashboard --write so the
    dashboard surfaces RED with links.
  - When clean: JSON status=ok; dashboard shows green for last deep scan
    (ops_dashboard.collect_security reads the JSON). Does not spam the
    dashboard with noise when green.

  python3 scripts/security_root_ioc_scan.py
  python3 scripts/security_root_ioc_scan.py --deep   # include containerd (sudo)
  sudo python3 scripts/security_root_ioc_scan.py --deep --write-dashboard

Schedule: deploy/security-root-ioc.timer (weekly).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HARNESS = Path(__file__).resolve().parents[1]
HKT = ZoneInfo("Asia/Hong_Kong")

# Known malicious seed versions (ChainDrop / related campaign)
MAL_SEED: dict[str, str] = {
    "keyv": "6.0.0",
    "flat-cache": "6.1.24",
    "file-entry-cache": "11.1.6",
    "cacheable": "2.5.1",
    "cacheable-request": "13.0.20",
    "cache-manager": "7.2.10",
    "ecto": "5.0.1",
    "@cacheable/net": "2.1.1",
    "@cacheable/node-cache": "3.1.2",
    "@cacheable/memory": "2.2.1",
    "@cacheable/utils": "2.5.1",
}

PAYLOAD_NAMES = (
    "Math_Symbol.js",
    "math_init.js",
    "gh-token-monitor.sh",
    "gh-token-monitor.service",
)

# setup.mjs only suspicious under keyv-ish trees
SETUP_MJS_HINTS = ("keyv", "flat-cache", "file-entry-cache", "cacheable")


def _vault() -> Path | None:
    raw = os.environ.get("PRODUCT_VAULT_ROOT", "").strip()
    if raw:
        p = Path(raw)
        if p.is_dir():
            return p
    for cand in (
        Path.home() / "second-brain" / "vault",
        Path("/opt/second-brain/vault"),  # last-resort host path
    ):
        if cand.is_dir():
            return cand
    return None


def _now_labels() -> tuple[str, str]:
    utc = datetime.now(timezone.utc)
    hkt = utc.astimezone(HKT)
    return (
        utc.strftime("%Y-%m-%d %H:%M UTC"),
        hkt.strftime("%Y-%m-%d %H:%M HKT"),
    )


def scan_lockfile(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return hits
    pkgs = data.get("packages") or data.get("dependencies") or {}
    if not isinstance(pkgs, dict):
        return hits
    for k, v in pkgs.items():
        if isinstance(v, dict):
            name = v.get("name") or str(k).split("node_modules/")[-1]
            ver = str(v.get("version") or "")
        elif isinstance(v, str):
            name = str(k)
            ver = v.lstrip("^~=")
        else:
            continue
        if name in MAL_SEED and ver == MAL_SEED[name]:
            hits.append(f"{name}@{ver} in {path}")
    return hits


def scan_tree(root: Path, *, max_depth: int | None = None) -> tuple[list[str], list[str]]:
    """Return (malicious_pins, payload_paths)."""
    pins: list[str] = []
    payloads: list[str] = []
    if not root.is_dir():
        return pins, payloads

    # Walk with depth limit to avoid pathological trees
    root_depth = len(root.parts)
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            p = Path(dirpath)
            depth = len(p.parts) - root_depth
            if max_depth is not None and depth > max_depth:
                dirnames.clear()
                continue
            # prune heavy/noise dirs
            skip = {
                ".git",
                "__pycache__",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                "htmlcov",
                "coverage",
                "playwright-report",
                "test-results",
            }
            dirnames[:] = [d for d in dirnames if d not in skip]

            for fn in filenames:
                fp = p / fn
                if fn == "package-lock.json" or fn == "npm-shrinkwrap.json":
                    # skip nested node_modules lock noise? still scan — pins matter
                    pins.extend(scan_lockfile(fp))
                if fn in PAYLOAD_NAMES:
                    payloads.append(str(fp))
                if fn == "setup.mjs":
                    s = str(fp).lower()
                    if any(h in s for h in SETUP_MJS_HINTS):
                        payloads.append(str(fp))
    except PermissionError:
        pass
    return pins, payloads


def run_scan(roots: list[Path], *, deep: bool) -> dict:
    all_pins: list[str] = []
    all_payloads: list[str] = []
    scanned: list[str] = []
    errors: list[str] = []

    for root in roots:
        if not root.exists():
            errors.append(f"missing:{root}")
            continue
        if not os.access(root, os.R_OK):
            errors.append(f"unreadable:{root}")
            continue
        depth = None if deep else 8
        pins, payloads = scan_tree(root, max_depth=depth)
        all_pins.extend(pins)
        all_payloads.extend(payloads)
        scanned.append(str(root))

    # de-dupe preserve order
    def uniq(xs: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    pins_u = uniq(all_pins)
    pay_u = uniq(all_payloads)
    status = "fail" if pins_u or pay_u else "ok"
    utc, hkt = _now_labels()
    return {
        "status": status,
        "when_utc": utc,
        "when_hkt": hkt,
        "deep": deep,
        "scanned_roots": scanned,
        "errors": errors,
        "malicious_pins": pins_u[:50],
        "payload_paths": pay_u[:50],
        "pin_count": len(pins_u),
        "payload_count": len(pay_u),
    }


def write_artifacts(vault: Path, result: dict) -> tuple[Path, Path]:
    vault.joinpath("agent-tasks").mkdir(parents=True, exist_ok=True)
    jpath = vault / "agent-tasks" / "security-ioc-last.json"
    mpath = vault / "agent-tasks" / "security-ioc-status.md"
    jpath.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    st = result["status"]
    emoji = "🔴" if st == "fail" else "🟢"
    lines = [
        "tags:",
        "  - type/ops",
        "  - domain/security",
        "  - ioc",
        "---",
        "",
        "# Security IoC scan (root / containerd)",
        "",
        f"**Status:** {emoji} **{st.upper()}**  ",
        f"**When:** {result['when_utc']} · {result['when_hkt']}  ",
        f"**Deep (containerd):** {result.get('deep')}  ",
        "**Generator:** `python3 scripts/security_root_ioc_scan.py`",
        "",
        "## Scanned roots",
        "",
    ]
    for r in result.get("scanned_roots") or []:
        lines.append(f"- `{r}`")
    if result.get("errors"):
        lines.extend(["", "## Errors / unreadable", ""])
        for e in result["errors"]:
            lines.append(f"- `{e}`")
    lines.extend(["", "## Findings", ""])
    if st == "ok":
        lines.append("No malicious seed pins or known payload filenames found.")
    else:
        if result.get("malicious_pins"):
            lines.append("### Malicious npm pins")
            for p in result["malicious_pins"]:
                lines.append(f"- `{p}`")
        if result.get("payload_paths"):
            lines.append("### Payload IoC paths")
            for p in result["payload_paths"]:
                lines.append(f"- `{p}`")
        lines.extend(
            [
                "",
                "## Action",
                "",
                "1. Do **not** execute unknown `setup.mjs` / `Math_Symbol.js`.",
                "2. Isolate host; remove package; rotate credentials.",
                "3. Re-run: `sudo python3 scripts/security_root_ioc_scan.py --deep`",
                "4. Open [[agent-tasks/OPS-DASHBOARD|OPS-DASHBOARD]] after refresh.",
            ]
        )
    lines.extend(
        [
            "",
            "## Ops front door",
            "",
            "Daily overview: [[agent-tasks/OPS-DASHBOARD|OPS-DASHBOARD]]",
            "",
            "_Auto-generated — do not hand-edit._",
            "",
        ]
    )
    mpath.write_text("\n".join(lines), encoding="utf-8")
    return jpath, mpath


def maybe_refresh_dashboard(force: bool, has_findings: bool) -> int:
    """Refresh OPS-DASHBOARD when findings or --write-dashboard."""
    if not force and not has_findings:
        return 0
    script = HARNESS / "scripts" / "ops_dashboard.py"
    if not script.is_file():
        return 0
    env = os.environ.copy()
    r = subprocess.run(
        [sys.executable, str(script), "--write"],
        cwd=str(HARNESS),
        env=env,
        check=False,
    )
    return int(r.returncode)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--deep",
        action="store_true",
        help="Include /var/lib/containerd and deeper walks (prefer sudo)",
    )
    ap.add_argument(
        "--root",
        action="append",
        default=[],
        help="Extra root to scan (repeatable)",
    )
    ap.add_argument(
        "--write-dashboard",
        action="store_true",
        help="Always re-run ops_dashboard --write after scan",
    )
    ap.add_argument(
        "--no-artifact",
        action="store_true",
        help="Print only; do not write vault artifacts",
    )
    args = ap.parse_args(argv)

    roots: list[Path] = [
        Path.home(),
        Path("/opt"),
    ]
    if args.deep:
        roots.append(Path("/var/lib/containerd"))
    for r in args.root:
        roots.append(Path(r).expanduser())

    result = run_scan(roots, deep=bool(args.deep))
    print(
        f"security_root_ioc status={result['status']} "
        f"pins={result['pin_count']} payloads={result['payload_count']} "
        f"deep={result['deep']} roots={len(result['scanned_roots'])}"
    )
    for e in result.get("errors") or []:
        print(f"  warn: {e}", file=sys.stderr)
    for p in (result.get("malicious_pins") or [])[:10]:
        print(f"  PIN {p}")
    for p in (result.get("payload_paths") or [])[:10]:
        print(f"  PAYLOAD {p}")

    vault = _vault()
    if not args.no_artifact:
        if not vault:
            print("No PRODUCT_VAULT_ROOT / vault — skip artifacts", file=sys.stderr)
        else:
            jpath, mpath = write_artifacts(vault, result)
            print(f"  wrote {jpath}")
            print(f"  wrote {mpath}")

    has_findings = result["status"] != "ok"
    # User request: notify dashboard when something found; always-refresh optional
    rc_dash = maybe_refresh_dashboard(
        force=bool(args.write_dashboard),
        has_findings=has_findings,
    )
    if has_findings or args.write_dashboard:
        print(f"  ops_dashboard refresh rc={rc_dash}")

    return 1 if has_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

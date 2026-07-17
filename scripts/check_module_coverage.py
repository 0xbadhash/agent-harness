#!/usr/bin/env python3
"""Per-module / fail-under coverage vs config/coverage_config.json (ORCH-P3b).

Modes:
  default / --config-only  Validate config shape (fast; used by validate.py).
  --run                    Run pytest+coverage (if installed) then enforce thresholds.
  --from-json PATH         Enforce against an existing coverage.json (no pytest).
  --soft-if-missing        Exit 0 with ⚠️ when coverage tooling is absent (night_shift).

Config keys:
  default      float — default minimum % for matched modules without override
  fail_under   float — overall TOTAL percent_covered floor (optional; default=default)
  modules      { path_prefix: min_pct } — 0 means skip that prefix
  exclude      list of glob-ish substrings to ignore in file paths
  source       list of packages/dirs for --cov (default: ["scripts"])
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "coverage_config.json"
DEFAULT_JSON = ROOT / ".agents" / "artifacts" / "coverage.json"


def load_cfg(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"⚠️  {path} missing — using default 80%")
        return {"default": 80, "modules": {}, "fail_under": 80, "exclude": [], "source": ["scripts"]}
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if "default" not in cfg or not isinstance(cfg["default"], (int, float)):
        raise ValueError("coverage_config.json missing numeric 'default'")
    cfg.setdefault("modules", {})
    cfg.setdefault("exclude", [])
    cfg.setdefault("source", ["scripts"])
    cfg.setdefault("fail_under", cfg["default"])
    return cfg


def _excluded(rel: str, exclude: list[str]) -> bool:
    for ex in exclude:
        ex = ex.replace("**/", "").replace("**", "").strip("*")
        if ex and ex in rel:
            return True
    return False


def _module_threshold(rel: str, modules: dict[str, Any], default: float) -> float | None:
    """Return min % for file, or None if skipped (threshold 0)."""
    best_key = ""
    best_val: float | None = default
    for prefix, thr in modules.items():
        p = str(prefix).replace("\\", "/").lstrip("./")
        if rel.startswith(p) or f"/{p}" in f"/{rel}":
            if len(p) >= len(best_key):
                best_key = p
                best_val = float(thr)
    if best_val is not None and best_val <= 0:
        return None
    return best_val if best_val is not None else default


def enforce_coverage_json(
    data: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Return (ok, messages)."""
    msgs: list[str] = []
    totals = data.get("totals") or {}
    total_pct = float(totals.get("percent_covered") or 0.0)
    fail_under = float(cfg.get("fail_under") or cfg["default"])
    if total_pct + 1e-9 < fail_under:
        msgs.append(f"❌ overall coverage {total_pct:.1f}% < fail_under {fail_under}%")
    else:
        msgs.append(f"✅ overall coverage {total_pct:.1f}% (fail_under {fail_under}%)")

    files = data.get("files") or {}
    modules = cfg.get("modules") or {}
    exclude = list(cfg.get("exclude") or [])
    default = float(cfg["default"])
    mod_hits: dict[str, list[float]] = {}

    for fpath, meta in files.items():
        rel = str(fpath).replace("\\", "/")
        # normalize to repo-relative if absolute
        if str(ROOT).replace("\\", "/") in rel:
            rel = rel.split(str(ROOT).replace("\\", "/") + "/", 1)[-1]
        if _excluded(rel, exclude):
            continue
        thr = _module_threshold(rel, modules, default)
        if thr is None:
            continue
        summary = meta.get("summary") or meta
        pct = float(summary.get("percent_covered") or 0.0)
        # aggregate by first matching module prefix for reporting
        key = "default"
        for prefix in modules:
            p = str(prefix).replace("\\", "/").lstrip("./")
            if rel.startswith(p):
                key = p
                break
        mod_hits.setdefault(key, []).append(pct)
        if pct + 1e-9 < thr:
            msgs.append(f"❌ {rel}: {pct:.1f}% < {thr}%")

    for key, pcts in sorted(mod_hits.items()):
        if not pcts:
            continue
        avg = sum(pcts) / len(pcts)
        thr = float(modules.get(key, default)) if key != "default" else default
        if thr <= 0:
            continue
        if avg + 1e-9 < thr:
            msgs.append(f"❌ module {key} avg {avg:.1f}% < {thr}% ({len(pcts)} files)")
        else:
            msgs.append(f"✅ module {key} avg {avg:.1f}% ≥ {thr}% ({len(pcts)} files)")

    ok = not any(m.startswith("❌") for m in msgs)
    return ok, msgs


def _coverage_available(py: str) -> bool:
    r = subprocess.run(
        [py, "-c", "import coverage, pytest"],
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode == 0


def run_pytest_coverage(
    py: str,
    cfg: dict[str, Any],
    out_json: Path,
) -> tuple[int, str]:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    sources = cfg.get("source") or ["scripts"]
    cmd = [py, "-m", "pytest", "-q", "--tb=no"]
    for src in sources:
        cmd.append(f"--cov={src}")
    cmd.extend(
        [
            f"--cov-report=json:{out_json}",
            "--cov-report=term-missing:skip-covered",
            "--cov-fail-under=0",  # we enforce thresholds ourselves
        ]
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, check=False)
    tail = ((r.stdout or "") + (r.stderr or ""))[-2000:]
    return r.returncode, tail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=CFG)
    ap.add_argument(
        "--config-only",
        action="store_true",
        help="Only validate config shape (default when --run not set)",
    )
    ap.add_argument(
        "--run",
        action="store_true",
        help="Run pytest with coverage and enforce thresholds",
    )
    ap.add_argument(
        "--from-json",
        type=Path,
        default=None,
        help="Enforce thresholds from existing coverage.json",
    )
    ap.add_argument(
        "--soft-if-missing",
        action="store_true",
        help="If coverage tooling missing, warn and exit 0",
    )
    ap.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON,
        help="Where --run writes coverage.json",
    )
    args = ap.parse_args(argv)

    try:
        cfg = load_cfg(args.config)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"❌ config error: {exc}")
        return 1

    # Config-only path (validate.py default)
    if not args.run and args.from_json is None:
        print(
            f"✅ coverage config valid (default {cfg['default']}%, "
            f"fail_under {cfg.get('fail_under')}%, "
            f"{len(cfg.get('modules') or {})} overrides)"
        )
        return 0

    py = str(ROOT / ".venv" / "bin" / "python")
    if not Path(py).is_file():
        py = sys.executable

    data_path = args.from_json
    if args.run:
        if not _coverage_available(py):
            msg = (
                "coverage/pytest not importable — install pytest-cov "
                "(pip install coverage pytest-cov)"
            )
            if args.soft_if_missing:
                print(f"⚠️  coverage skip: {msg}")
                return 0
            print(f"❌ {msg}")
            return 1
        code, tail = run_pytest_coverage(py, cfg, args.json_out)
        if code != 0 and not args.json_out.is_file():
            print(f"❌ pytest --cov failed (exit {code})")
            print(tail)
            return 1
        if code != 0:
            print(f"⚠️  pytest exit {code} but coverage.json present — enforcing anyway")
        data_path = args.json_out

    assert data_path is not None
    if not data_path.is_file():
        print(f"❌ coverage json missing: {data_path}")
        return 1

    data = json.loads(data_path.read_text(encoding="utf-8"))
    ok, msgs = enforce_coverage_json(data, cfg)
    for m in msgs:
        print(m)
    if ok:
        print("✅ coverage thresholds met")
        return 0
    print("❌ coverage threshold failure(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

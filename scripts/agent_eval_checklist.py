#!/usr/bin/env python3
"""C5 — lightweight agent skill-conformance checklist (not LLM-as-judge).

Runs portable checks against a harness/product root:
  1. pipeline_state get (script present)
  2. next_skill --after execute_dev prints NEXT_SKILL=
  3. hard_gates --help
  4. optional: unittest subset (fsm / hard_gates / next_skill) when tests/ exists

Exit 0 if all selected checks pass.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class EvalResult:
    ok: bool
    checks: list[CheckResult] = field(default_factory=list)


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return int(r.returncode), out
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as e:
        return 127, str(e)


def evaluate(root: Path, *, run_tests: bool = True) -> EvalResult:
    root = root.resolve()
    checks: list[CheckResult] = []
    scripts = root / "scripts"
    py = sys.executable

    # 1 pipeline_state
    ps = scripts / "pipeline_state.py"
    if not ps.is_file():
        checks.append(CheckResult("pipeline_state", False, "missing scripts/pipeline_state.py"))
    else:
        rc, out = _run([py, str(ps), "get"], root)
        checks.append(
            CheckResult(
                "pipeline_state",
                rc == 0 and ("phase" in out.lower() or "{" in out),
                out.strip()[:200],
            )
        )

    # 2 next_skill
    ns = scripts / "next_skill.py"
    if not ns.is_file():
        checks.append(CheckResult("next_skill", False, "missing"))
    else:
        rc, out = _run([py, str(ns), "--after", "execute_dev"], root)
        ok = rc == 0 and "NEXT_SKILL=" in out
        checks.append(CheckResult("next_skill", ok, out.strip().splitlines()[-1] if out else ""))

    # 3 hard_gates help
    hg = scripts / "hard_gates.py"
    if not hg.is_file():
        checks.append(CheckResult("hard_gates", False, "missing"))
    else:
        rc, out = _run([py, str(hg), "--help"], root)
        checks.append(CheckResult("hard_gates", rc == 0, "help ok" if rc == 0 else out[:120]))

    # 4 optional unittest subset
    if run_tests and (root / "tests").is_dir():
        mods = []
        for name in (
            "tests.test_fsm_conformance",
            "tests.test_hard_gates",
            "tests.test_next_skill",
        ):
            # only if module file exists (tests/test_x.py)
            parts = name.split(".")
            path = root.joinpath(*parts[:-1], parts[-1] + ".py")
            if path.is_file():
                mods.append(name)
        if mods:
            rc, out = _run([py, "-m", "unittest", *mods, "-q"], root, timeout=300)
            checks.append(
                CheckResult(
                    "unittest_subset",
                    rc == 0,
                    f"rc={rc} mods={len(mods)}",
                )
            )
        else:
            checks.append(CheckResult("unittest_subset", True, "no subset modules (skip)"))
    elif run_tests:
        checks.append(CheckResult("unittest_subset", True, "no tests/ (skip)"))

    ok = all(c.ok for c in checks)
    return EvalResult(ok=ok, checks=checks)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args(argv)
    r = evaluate(args.root, run_tests=not args.skip_tests)
    print(f"agent_eval_checklist ok={r.ok}")
    for c in r.checks:
        mark = "✅" if c.ok else "❌"
        print(f"  {mark} {c.name}: {c.detail}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded auto-fix helpers for night_shift readiness (ORCH-P3).

**Allowed:** mechanical fixes that restore readiness (deps, formatters, lockfile install).
**Forbidden:** inventing product features, release/tag/push, broad refactors, secret changes.

Used by ``night_shift_readiness.py`` after a failed gate pass; re-run gates once.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
            check=False,
        )
        return {
            "cmd": cmd,
            "exit": r.returncode,
            "ok": r.returncode == 0,
            "stdout_tail": (r.stdout or "")[-1200:],
            "stderr_tail": (r.stderr or "")[-600:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "cmd": cmd,
            "exit": 124,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def _venv_python(root: Path) -> str:
    for rel in (".venv/bin/python", "venv/bin/python", ".venv/bin/python3", "venv/bin/python3"):
        p = root / rel
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return sys.executable


def _combined_tails(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for r in results:
        if r.get("ok"):
            continue
        parts.append(r.get("stdout_tail") or "")
        parts.append(r.get("stderr_tail") or "")
        parts.append(r.get("name") or "")
    return "\n".join(parts)


def try_ensure_dev_env(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    """Install product venv / requirements-dev when gates fail on missing deps."""
    scripts = root / "scripts"
    ensure = scripts / "ensure_product_dev_env.py"
    harness_ensure = Path(__file__).resolve().parent / "ensure_product_dev_env.py"
    target = ensure if ensure.is_file() else harness_ensure
    if not target.is_file():
        # inline minimal: requirements-dev + venv
        req = root / "requirements-dev.txt"
        if not req.is_file():
            return None
        py = _venv_python(root)
        if dry_run:
            return {
                "name": "ensure_dev_env",
                "ok": True,
                "dry_run": True,
                "detail": f"would pip install -r {req} with {py}",
            }
        venv = root / ".venv"
        if not (venv / "bin" / "python").is_file():
            _run([sys.executable, "-m", "venv", str(venv)], cwd=root, timeout=120)
            py = str(venv / "bin" / "python")
        r = _run([py, "-m", "pip", "install", "-r", str(req)], cwd=root, timeout=1200)
        r["name"] = "ensure_dev_env"
        r["detail"] = "pip install -r requirements-dev.txt"
        return r

    py = sys.executable
    if dry_run:
        return {
            "name": "ensure_dev_env",
            "ok": True,
            "dry_run": True,
            "detail": f"would run {target}",
        }
    # ensure_product_dev_env may be importable
    if target.name == "ensure_product_dev_env.py":
        sys.path.insert(0, str(target.parent))
        try:
            from ensure_product_dev_env import ensure_product_dev_env  # type: ignore

            out = ensure_product_dev_env(root, dry_run=False)
            return {
                "name": "ensure_dev_env",
                "ok": bool(out.get("ok")),
                "exit": 0 if out.get("ok") else 1,
                "detail": str(out.get("message") or out.get("status") or out),
                "stdout_tail": str(out)[:800],
                "stderr_tail": "",
            }
        except Exception as exc:  # noqa: BLE001
            r = _run([py, str(target), str(root)], cwd=root, timeout=1200)
            r["name"] = "ensure_dev_env"
            r["detail"] = f"script fallback after import err: {exc}"
            return r
    r = _run([py, str(target)], cwd=root, timeout=1200)
    r["name"] = "ensure_dev_env"
    return r


def try_npm_ci(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    if not (root / "package.json").is_file():
        return None
    if dry_run:
        return {
            "name": "npm_install",
            "ok": True,
            "dry_run": True,
            "detail": "would npm ci || npm install",
        }
    if (root / "package-lock.json").is_file():
        r = _run(["npm", "ci"], cwd=root, timeout=1200)
        if r["ok"]:
            r["name"] = "npm_install"
            r["detail"] = "npm ci"
            return r
    r = _run(["npm", "install"], cwd=root, timeout=1200)
    r["name"] = "npm_install"
    r["detail"] = "npm install"
    return r


def try_ruff_fix(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    py = _venv_python(root)
    # ruff check --fix on scripts/ and tests/ only (bounded)
    targets = [p for p in ("scripts", "tests", "src") if (root / p).is_dir()]
    if not targets:
        return None
    cmd = [py, "-m", "ruff", "check", "--fix", *targets]
    if dry_run:
        return {
            "name": "ruff_fix",
            "ok": True,
            "dry_run": True,
            "detail": " ".join(cmd),
        }
    r = _run(cmd, cwd=root, timeout=300)
    if r["exit"] == 127 or "No module named ruff" in (r.get("stderr_tail") or ""):
        return None
    r["name"] = "ruff_fix"
    r["detail"] = "ruff check --fix (scripts/tests/src)"
    return r


def try_black_format(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    py = _venv_python(root)
    targets = [p for p in ("scripts", "tests") if (root / p).is_dir()]
    if not targets:
        return None
    cmd = [py, "-m", "black", *targets]
    if dry_run:
        return {
            "name": "black_format",
            "ok": True,
            "dry_run": True,
            "detail": " ".join(cmd),
        }
    r = _run(cmd, cwd=root, timeout=300)
    if r["exit"] == 127 or "No module named black" in (r.get("stderr_tail") or ""):
        return None
    r["name"] = "black_format"
    r["detail"] = "black scripts/ tests/"
    return r


def try_trailing_whitespace(root: Path, *, dry_run: bool) -> dict[str, Any] | None:
    """Strip trailing whitespace on recently modified text files under scripts/ (bounded)."""
    scripts = root / "scripts"
    if not scripts.is_dir():
        return None
    changed = 0
    files: list[Path] = []
    for p in scripts.rglob("*.py"):
        if p.name.startswith("."):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = text.splitlines(keepends=True)
        new_lines = [re.sub(r"[ \t]+(\r?\n)", r"\1", ln) for ln in lines]
        new = "".join(new_lines)
        if new != text:
            files.append(p)
            if not dry_run:
                p.write_text(new, encoding="utf-8")
            changed += 1
    if not changed:
        return None
    return {
        "name": "trailing_whitespace",
        "ok": True,
        "exit": 0,
        "dry_run": dry_run,
        "detail": f"{'would strip' if dry_run else 'stripped'} trailing ws in {changed} script(s)",
        "stdout_tail": "\n".join(str(f.relative_to(root)) for f in files[:20]),
        "stderr_tail": "",
    }


def attempt_autofix(
    root: Path,
    results: list[dict[str, Any]],
    *,
    dry_run: bool = False,
    product_id: str = "",
) -> list[dict[str, Any]]:
    """Run bounded fixers relevant to failed gates. Returns list of attempt records."""
    failed = [r for r in results if not r.get("ok")]
    if not failed:
        return []

    names = {r.get("name") for r in failed}
    tails = _combined_tails(results).lower()
    attempts: list[dict[str, Any]] = []

    need_deps = bool(
        names & {"validate_full", "product_smoke", "coverage", "security_pytest"}
    ) or any(
        k in tails
        for k in (
            "modulenotfounderror",
            "no module named",
            "cannot find module",
            "err_module_not_found",
            "cannot find package",
        )
    )
    if need_deps:
        a = try_ensure_dev_env(root, dry_run=dry_run)
        if a:
            attempts.append(a)

    if "product_smoke" in names or "validate_full" in names:
        if (root / "package.json").is_file() and any(
            k in tails
            for k in (
                "cannot find module",
                "err_module_not_found",
                "npm err",
                "enoent",
                "node_modules",
            )
        ):
            a = try_npm_ci(root, dry_run=dry_run)
            if a:
                attempts.append(a)

    if names & {"repo_hygiene", "validate_full", "hardcodes"}:
        a = try_ruff_fix(root, dry_run=dry_run)
        if a:
            attempts.append(a)
        a = try_black_format(root, dry_run=dry_run)
        if a:
            attempts.append(a)
        a = try_trailing_whitespace(root, dry_run=dry_run)
        if a:
            attempts.append(a)

    # Annotate product id for logs
    for a in attempts:
        a["product_id"] = product_id
    return attempts

# Lean muda (waste) labels — only when evidence maps cleanly.
LEAN_LABELS = {
    "defect": "defect",
    "rework": "rework",
    "inventory": "inventory",
    "overprocessing": "overprocessing",
    "waiting": "waiting",
    "motion": "motion",
    "overproduction": "overproduction",
}


def _clamp_confidence(x: float) -> float:
    """Normalize confidence to [0.0, 1.0] (0=lowest, 1=highest)."""
    return max(0.0, min(1.0, round(float(x), 2)))


def _format_proposal(
    product_id: str,
    *,
    confidence: float,
    kind: str,
    lean: str,
    action: str,
    evidence: list[str],
) -> str:
    """Standard proposal line for TODO / recs.

    confidence: 0.0 = weak/inferred … 1.0 = direct gate/file evidence.
    kind: fix | refactor | standardize | normalize | lean_waste | ops | security
    lean: muda label (defect, rework, inventory, overprocessing, waiting, motion, …)
    """
    conf = _clamp_confidence(confidence)
    facts = "; ".join(e.strip() for e in evidence if e and e.strip())[:320]
    return (
        f"[{product_id}] PROPOSE confidence={conf:.2f} kind={kind} lean={lean} | "
        f"{action} | evidence: {facts}"
    )


def _tail_of(r: dict[str, Any], n: int = 500) -> str:
    return ((r.get("stderr_tail") or "") + "\n" + (r.get("stdout_tail") or ""))[:n]


def _refactor_signals(tail: str) -> list[tuple[str, float, str]]:
    """(action, conf_boost, lean) from failure tails — fact patterns only."""
    low = tail.lower()
    hits: list[tuple[str, float, str]] = []
    patterns: list[tuple[str, str, float, str]] = [
        (
            r"deprecated|deprecationwarning",
            "refactor: remove or replace deprecated APIs",
            0.15,
            "rework",
        ),
        (
            r"magicmock|over-?mock",
            "refactor: reduce MagicMock / tighten real boundaries (hygiene)",
            0.20,
            "overprocessing",
        ),
        (
            r"duplicate|duplicat|copy-?paste|identical",
            "refactor: normalize duplicated modules into one shared path",
            0.18,
            "overprocessing",
        ),
        (
            r"too complex|cyclomatic|cognitive complexity|c901",
            "refactor: split high-complexity functions (standardize structure)",
            0.22,
            "overprocessing",
        ),
        (
            r"unused import|f401|is defined but never used",
            "lean: delete unused imports/dead symbols (waste=inventory)",
            0.25,
            "inventory",
        ),
        (
            r"todo|fixme|xxx",
            "refactor: resolve in-code TODO/FIXME flagged by gates",
            0.12,
            "rework",
        ),
        (
            r"absolute path|/home/|[a-z]:\\\\",
            "standardize: replace absolute host paths with portable roots",
            0.20,
            "motion",
        ),
        (
            r"line too long|e501",
            "standardize: format long lines (ruff/black) — low-waste hygiene",
            0.10,
            "overprocessing",
        ),
    ]
    for rx, action, boost, lean in patterns:
        if re.search(rx, low):
            hits.append((action, boost, lean))
    return hits


def propose_roadmap_items(
    root: Path,
    results: list[dict[str, Any]],
    matrix_missing: list[str],
    product_id: str,
) -> list[str]:
    """Evidence-based roadmap *proposals* only — never invent greenfield features.

    Each line is normalized as::

        [id] PROPOSE confidence=0.00..1.00 kind=… lean=… | action | evidence: …

    Confidence is fact-weighted (gate fail, path exists, open AC, tail patterns).
    Refactor / standardize / lean-waste proposals appear only when gates or
    matrix/PRD evidence support them.
    """
    proposals: list[str] = []
    failed = [r for r in results if not r.get("ok")]
    failed_names = {str(r.get("name") or "") for r in failed}

    # Matrix gaps: restore OR retire (lean inventory of dead tests)
    for miss in matrix_missing[:8]:
        conf = 0.88
        proposals.append(
            _format_proposal(
                product_id,
                confidence=conf,
                kind="lean_waste",
                lean="inventory",
                action=(
                    f"restore missing test surface `{miss}` or retire the matrix row "
                    f"(standardize TEST_MATRIX to match reality)"
                ),
                evidence=[
                    f"TEST_MATRIX missing path `{miss}`",
                    "check_test_matrix / night_shift matrix scan",
                ],
            )
        )
        proposals.append(
            _format_proposal(
                product_id,
                confidence=_clamp_confidence(conf - 0.08),
                kind="refactor",
                lean="overprocessing",
                action=(
                    f"if `{miss}` is obsolete, delete dead scaffolding and normalize "
                    f"matrix — avoid maintaining unused inventory"
                ),
                evidence=[
                    f"missing path `{miss}` with no auto-created file",
                    "lean: unused test inventory is muda",
                ],
            )
        )

    for r in failed:
        name = str(r.get("name") or "")
        exit_code = r.get("exit")
        tail = _tail_of(r)
        base_conf = 0.70
        if exit_code not in (None, 0):
            base_conf = min(0.95, base_conf + 0.10)

        if name == "product_smoke":
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=base_conf + 0.08,
                    kind="fix",
                    lean="defect",
                    action=(
                        "repair product_plugin smoke[] or restore failing build/start "
                        "command (do not invent new smoke without plugin evidence)"
                    ),
                    evidence=[
                        f"product_smoke exit={exit_code}",
                        (tail[:120] or "smoke stderr empty").replace("\n", " "),
                    ],
                )
            )
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=0.55,
                    kind="standardize",
                    lean="rework",
                    action=(
                        "standardize smoke steps across products (same argv shape in "
                        "product_plugin.yaml) once this product's smoke is green"
                    ),
                    evidence=[
                        "product_smoke failed",
                        "plugin-driven smoke is the portable contract",
                    ],
                )
            )
        elif name == "coverage":
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=base_conf + 0.05,
                    kind="fix",
                    lean="defect",
                    action=(
                        "raise tests on failing modules OR normalize "
                        "config/coverage_config.json fail_under to measured reality"
                    ),
                    evidence=[
                        f"coverage gate exit={exit_code}",
                        (tail[:120] or "coverage report").replace("\n", " "),
                    ],
                )
            )
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=0.62,
                    kind="refactor",
                    lean="overprocessing",
                    action=(
                        "refactor hard-to-test modules that force coverage workarounds "
                        "(only if coverage names specific modules in output)"
                    ),
                    evidence=[
                        "coverage gate failed",
                        "refactor only where module list is in gate tail",
                    ],
                )
            )
        elif name.startswith("security"):
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=min(0.98, base_conf + 0.20),
                    kind="security",
                    lean="defect",
                    action=(
                        f"P0: remediate security gate `{name}` before feature work "
                        f"(no new roadmap invent until green)"
                    ),
                    evidence=[
                        f"security gate `{name}` exit={exit_code}",
                        (tail[:140] or "security failure").replace("\n", " "),
                    ],
                )
            )
        elif name.startswith("live_http") or name == "static_denies_live":
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=base_conf,
                    kind="ops",
                    lean="waiting",
                    action=(
                        f"ops: restore live probe `{name}` (app/fpm/DNS/nginx denies) "
                        f"— not a product feature invent"
                    ),
                    evidence=[
                        f"`{name}` exit={exit_code}",
                        (tail[:120] or "HTTP/nginx").replace("\n", " "),
                    ],
                )
            )
        elif name == "hardcodes":
            is_secret = "secret" in tail.lower()
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=min(0.97, base_conf + (0.15 if is_secret else 0.05)),
                    kind="security" if is_secret else "standardize",
                    lean="defect" if is_secret else "motion",
                    action=(
                        "remove secrets/absolute paths; standardize on env + portable roots"
                    ),
                    evidence=[
                        f"hardcodes exit={exit_code}",
                        (tail[:140] or "hardcode hit").replace("\n", " "),
                    ],
                )
            )
        elif name == "repo_hygiene":
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=base_conf,
                    kind="standardize",
                    lean="overprocessing",
                    action=(
                        "normalize repo hygiene (MagicMock/TODO policy, cruft) — "
                        "lean: stop shipping process waste"
                    ),
                    evidence=[
                        f"repo_hygiene exit={exit_code}",
                        (tail[:120] or "hygiene").replace("\n", " "),
                    ],
                )
            )
        elif name == "validate_full":
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=base_conf + 0.05,
                    kind="fix",
                    lean="defect",
                    action=(
                        "clear validate full (type/lint/test/hardcode) before next "
                        "/execute_dev"
                    ),
                    evidence=[
                        f"validate_full exit={exit_code}",
                        (tail[:120] or "validate").replace("\n", " "),
                    ],
                )
            )
        elif name == "test_matrix":
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=base_conf + 0.08,
                    kind="standardize",
                    lean="inventory",
                    action="normalize TEST_MATRIX rows to files that exist (or add tests)",
                    evidence=[
                        f"test_matrix exit={exit_code}",
                        (tail[:120] or "matrix").replace("\n", " "),
                    ],
                )
            )
        else:
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=max(0.40, base_conf - 0.15),
                    kind="fix",
                    lean="defect",
                    action=f"investigate failed gate `{name}` and restore green",
                    evidence=[
                        f"gate `{name}` exit={exit_code}",
                        (tail[:100] or "see NIGHT_SHIFT_REPORT").replace("\n", " "),
                    ],
                )
            )

        for action, boost, lean in _refactor_signals(tail)[:3]:
            kind = "refactor" if action.startswith("refactor") else (
                "standardize" if action.startswith("standardize") else "lean_waste"
            )
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=_clamp_confidence(0.45 + boost + 0.15),
                    kind=kind,
                    lean=lean,
                    action=action,
                    evidence=[
                        f"gate `{name}` tail pattern match",
                        f"snippet: {tail[:80].replace(chr(10), ' ')}",
                    ],
                )
            )

    # Explicit open AC (not invented)
    for rel in ("memory/PRD.md", ".agents/BACKLOG.md", "docs/ROADMAP.md", "ROADMAP.md"):
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        opens = re.findall(r"^\s*- \[ \] (.+)$", text, re.M)
        for item in opens[:5]:
            item = item.strip()
            if len(item) < 8:
                continue
            conf = 0.90
            if failed_names & {"product_smoke", "validate_full"} and re.search(
                r"build|smoke|test|type", item, re.I
            ):
                conf = 0.95
            proposals.append(
                _format_proposal(
                    product_id,
                    confidence=conf,
                    kind="fix",
                    lean="waiting",
                    action=f"close existing open AC: {item[:100]}",
                    evidence=[
                        f"unchecked box in {rel}",
                        "not invented — already on product roadmap",
                    ],
                )
            )

    def _conf_key(line: str) -> float:
        m = re.search(r"confidence=([0-9.]+)", line)
        return float(m.group(1)) if m else 0.0

    proposals.sort(key=_conf_key, reverse=True)
    seen: set[str] = set()
    out: list[str] = []
    for p in proposals:
        action_key = p.split("|", 2)[1].strip() if p.count("|") >= 2 else p
        if action_key in seen:
            continue
        seen.add(action_key)
        out.append(p)
    return out[:16]

#!/usr/bin/env python3
"""ORCH-P3 readiness night runner (harness SoT) — per-product gates + vault TODO.

**Source of truth:** agent-harness. Products receive this via install_into_product.sh.

**Read-only for product code.** Never tags, never pushes, never /release_mgmt.

Writes (per product root):
  - .agents/artifacts/NIGHT_SHIFT_REPORT.md
  - .agents/artifacts/NIGHT_SHIFT_TODO.md
  - vault 01-Projects/<project_label>/night-shift-log.md
  - vault 01-Projects/<project_label>/TODO.md
  - vault agent-tasks/kanban.md Done note when overall PASS (auto:night_shift_readiness)
  - optional vault ad-hoc note via sync_vault_devlog.py when present

Exit 0 = all gates pass; 1 = one or more failures (still writes reports).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# When installed into a product, this file lives at <product>/scripts/
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
ARTIFACTS = ROOT / ".agents" / "artifacts"
DEFAULT_VAULT = Path("/opt/second-brain/vault")
KANBAN_AUTO_MARKER = "auto:night_shift_readiness"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _run(
    name: str,
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 3600,
    env: dict | None = None,
) -> dict[str, Any]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
        )
        return {
            "name": name,
            "cmd": cmd,
            "exit": r.returncode,
            "ok": r.returncode == 0,
            "stdout_tail": (r.stdout or "")[-1500:],
            "stderr_tail": (r.stderr or "")[-800:],
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "cmd": cmd,
            "exit": 124,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": f"timeout after {timeout}s",
        }
    except FileNotFoundError as exc:
        return {
            "name": name,
            "cmd": cmd,
            "exit": 127,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def _venv_python(root: Path = ROOT) -> str:
    """Prefer project virtualenv (``.venv`` or ``venv``), else current interpreter."""
    for candidate in (
        root / ".venv" / "bin" / "python",
        root / "venv" / "bin" / "python",
        root / ".venv" / "bin" / "python3",
        root / "venv" / "bin" / "python3",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _load_plugin(root: Path = ROOT) -> dict[str, Any]:
    path = root / ".agents" / "product_plugin.yaml"
    if not path.is_file():
        return {}
    # minimal parse without requiring PyYAML
    data: dict[str, Any] = {}
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^product_id:\s*(\S+)", text, re.M)
    if m:
        data["product_id"] = m.group(1).strip().strip("\"'")
    # vault block
    vault: dict[str, Any] = {}
    in_vault = False
    for line in text.splitlines():
        if re.match(r"^vault:\s*$", line):
            in_vault = True
            continue
        if in_vault and re.match(r"^[a-zA-Z_]", line) and not line.startswith(" "):
            break
        if not in_vault:
            continue
        km = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.*)$", line)
        if not km:
            continue
        key, val = km.group(1), km.group(2).strip()
        if key == "mirror_docs" or val == "" or val == "[]":
            continue
        if val.lower() in ("true", "false"):
            vault[key] = val.lower() == "true"
        else:
            vault[key] = val.strip("\"'")
    if vault:
        data["vault"] = vault
    # night_shift optional
    ns: dict[str, Any] = {}
    in_ns = False
    live_urls: list[str] = []
    in_urls = False
    for line in text.splitlines():
        if re.match(r"^night_shift:\s*$", line):
            in_ns = True
            in_urls = False
            continue
        if in_ns and re.match(r"^[a-zA-Z_]", line) and not line.startswith(" "):
            break
        if not in_ns:
            continue
        if re.match(r"^\s+live_urls:\s*$", line):
            in_urls = True
            continue
        if in_urls:
            um = re.match(r"^\s+-\s+(\S+)", line)
            if um:
                live_urls.append(um.group(1).strip().strip("\"'"))
            elif re.match(r"^\s+[a-zA-Z_]", line):
                in_urls = False
        km = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.*)$", line)
        if km and km.group(1) != "live_urls":
            ns[km.group(1)] = km.group(2).strip().strip("\"'")
    if live_urls:
        ns["live_urls"] = live_urls
    if ns:
        data["night_shift"] = ns
    return data


def _vault_project_rel(plugin: dict[str, Any]) -> Path:
    vault = plugin.get("vault") or {}
    label = (
        vault.get("project_label")
        or plugin.get("product_id")
        or ROOT.name
    )
    return Path("01-Projects") / str(label)


def _vault_root(plugin: dict[str, Any], cli_vault: Path | None) -> Path:
    if cli_vault is not None:
        return cli_vault
    vault = plugin.get("vault") or {}
    env_key = vault.get("root_env") or "PRODUCT_VAULT_ROOT"
    for key in (env_key, "WATCHLIST_VAULT_ROOT", "PRODUCT_VAULT_ROOT"):
        if key and os.environ.get(key):
            return Path(os.environ[key])
    default = vault.get("default_root") or str(DEFAULT_VAULT)
    return Path(default) if default else DEFAULT_VAULT


def run_gates(
    *,
    quick: bool = False,
    skip_live: bool = False,
    plugin: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run readiness gates. Skips missing tools (portable across products)."""
    plugin = plugin or {}
    py = _venv_python()
    results: list[dict[str, Any]] = []

    def add_if(script: str, name: str, args: list[str] | None = None, **kw: Any) -> None:
        path = SCRIPTS / script
        if not path.is_file():
            return
        results.append(
            _run(name, [py, str(path), *(args or [])], timeout=kw.get("timeout", 600))
        )

    matrix = ROOT / ".agents" / "policy" / "TEST_MATRIX.md"
    if matrix.is_file() and (SCRIPTS / "check_test_matrix.py").is_file():
        results.append(
            _run(
                "test_matrix",
                [py, str(SCRIPTS / "check_test_matrix.py")],
                timeout=60,
            )
        )
    elif matrix.is_file():
        results.append(
            {
                "name": "test_matrix",
                "cmd": [],
                "exit": 0,
                "ok": True,
                "stdout_tail": "matrix present but checker missing — skipped",
                "stderr_tail": "",
            }
        )

    add_if("check_repo_hygiene.py", "repo_hygiene", timeout=120)
    add_if("check_hardcodes.py", "hardcodes", timeout=120)
    add_if("verify_skills.py", "verify_skills", timeout=60)

    if quick:
        if not results:
            results.append(
                {
                    "name": "no_gates",
                    "cmd": [],
                    "exit": 0,
                    "ok": True,
                    "stdout_tail": "no harness gate scripts found",
                    "stderr_tail": "",
                }
            )
        return results

    if (SCRIPTS / "validate.py").is_file():
        ns = plugin.get("night_shift") or {}
        vmode = str(ns.get("validate_mode") or "full").strip().lower()
        if vmode not in {"full", "night", "hygiene"}:
            vmode = "full"
        results.append(
            _run(
                "validate_full",
                [py, str(SCRIPTS / "validate.py"), vmode],
                # Large products (e.g. ocr-ledger full mypy+pytest cov) need >10m
                timeout=int(ns.get("validate_timeout", 1800 if vmode == "full" else 300)),
            )
        )
    if (SCRIPTS / "product_smoke.py").is_file():
        results.append(
            _run(
                "product_smoke",
                [py, str(SCRIPTS / "product_smoke.py"), "--root", str(ROOT)],
                timeout=900,
            )
        )

    # ORCH-P3b: real coverage thresholds (soft skip if pytest-cov not installed)
    if (SCRIPTS / "check_module_coverage.py").is_file():
        ns = plugin.get("night_shift") or {}
        soft = str(ns.get("coverage_soft", "1")).lower() not in ("0", "false", "no")
        do_run = str(ns.get("coverage_run", "1")).lower() not in ("0", "false", "no")
        cov_args: list[str] = []
        if do_run:
            cov_args.append("--run")
        if soft:
            cov_args.append("--soft-if-missing")
        # Prefer existing coverage.json when not forcing a long pytest run
        if not do_run and (ROOT / "coverage.json").is_file():
            cov_args.extend(["--json-report", str(ROOT / "coverage.json")])
        results.append(
            _run(
                "coverage",
                [py, str(SCRIPTS / "check_module_coverage.py"), *cov_args],
                timeout=900,
            )
        )

    # Optional security pytest files if present
    sec_py = [
        p
        for p in (
            ROOT / "tests" / "test_security_auditing_for_api_key_leak_prevention.py",
            ROOT / "tests" / "test_obfuscate_api_key_leakages.py",
        )
        if p.is_file()
    ]
    if sec_py:
        results.append(
            _run(
                "security_pytest",
                [py, "-m", "pytest", "-q", *[str(p.relative_to(ROOT)) for p in sec_py]],
                env={**os.environ, "PYTHONPATH": str(ROOT)},
                timeout=300,
            )
        )

    # Optional PHPUnit security if migration layout
    sec_php = ROOT / "migration" / "tests" / "SecurityExposureTest.php"
    phpunit = ROOT / "migration" / "vendor" / "bin" / "phpunit"
    if sec_php.is_file() and phpunit.is_file():
        results.append(
            _run(
                "security_phpunit",
                [str(phpunit), "tests/SecurityExposureTest.php"],
                cwd=ROOT / "migration",
                timeout=300,
            )
        )

    if not skip_live:
        # Product-declared live URLs (plugin) or env BASE_URL + watchlist-style deny script
        ns = plugin.get("night_shift") or {}
        live_urls: list[str] = list(ns.get("live_urls") or [])
        base = (os.environ.get("PRODUCT_BASE_URL") or os.environ.get("WATCHLIST_BASE_URL") or "").strip()
        deny_sh = ROOT / "migration" / "deploy" / "verify-static-denies.sh"
        if deny_sh.is_file():
            if not base:
                # product may set PRODUCT_BASE_URL; split avoids hardcode scanners when set in unit
                host = (ns.get("default_host") or "").strip()
                if host:
                    base = "https://" + host if not host.startswith("http") else host
            if base:
                results.append(
                    _run(
                        "static_denies_live",
                        ["bash", str(deny_sh)],
                        env={**os.environ, "BASE_URL": base},
                        timeout=120,
                    )
                )
        for i, url in enumerate(live_urls):
            results.append(
                _run(
                    f"live_http_{i}",
                    [
                        "curl",
                        "-sS",
                        "-o",
                        "/dev/null",
                        "-w",
                        "%{http_code}",
                        "--max-time",
                        "20",
                        url,
                    ],
                    timeout=30,
                )
            )
            last = results[-1]
            if last["ok"]:
                code = (last.get("stdout_tail") or "").strip()
                expect = str(ns.get("live_expect_code") or "200")
                if code != expect:
                    last["ok"] = False
                    last["exit"] = 1
                    last["stderr_tail"] = f"HTTP {code} expected {expect}"

        # Single path under base when no live_urls but base set (generic smoke URL)
        path = (ns.get("live_path") or "").strip()
        if base and path and not live_urls:
            url = base.rstrip("/") + "/" + path.lstrip("/")
            results.append(
                _run(
                    "live_http",
                    [
                        "curl",
                        "-sS",
                        "-o",
                        "/dev/null",
                        "-w",
                        "%{http_code}",
                        "--max-time",
                        "20",
                        url,
                    ],
                    timeout=30,
                )
            )
            last = results[-1]
            if last["ok"]:
                code = (last.get("stdout_tail") or "").strip()
                if code != "200":
                    last["ok"] = False
                    last["exit"] = 1
                    last["stderr_tail"] = f"HTTP {code} expected 200"

    if not results:
        results.append(
            {
                "name": "no_gates",
                "cmd": [],
                "exit": 1,
                "ok": False,
                "stdout_tail": "",
                "stderr_tail": "no gates available — install harness scripts + smoke",
            }
        )
    return results


def recommendations_from(
    results: list[dict[str, Any]], matrix_missing: list[str], product_id: str
) -> list[str]:
    recs: list[str] = []
    failed = [r for r in results if not r["ok"]]
    if not failed and not matrix_missing:
        recs.append(
            f"[{product_id}] All readiness gates green — safe to start next product "
            f"`/execute_dev` (set AC in product roadmap Shaping)."
        )
        recs.append(
            f"[{product_id}] Optional: refresh golden fixtures after large refactors."
        )
        return recs

    for r in failed:
        name = r["name"]
        if name == "test_matrix":
            recs.append(
                f"[{product_id}] Restore missing tests in `.agents/policy/TEST_MATRIX.md` "
                "or update the matrix if surface was removed."
            )
        elif name == "product_smoke":
            recs.append(
                f"[{product_id}] Fix failing smoke steps in product_plugin.yaml before product work."
            )
        elif name == "validate_full":
            recs.append(
                f"[{product_id}] Run `python3 scripts/validate.py full`; fix type/lint/test/hardcode."
            )
        elif name.startswith("security"):
            recs.append(
                f"[{product_id}] Security gate `{name}` failed — treat as P0; see report tails."
            )
        elif name == "static_denies_live":
            recs.append(
                f"[{product_id}] Live nginx denies failed — fix include + reload nginx."
            )
        elif name.startswith("live_http"):
            recs.append(
                f"[{product_id}] Live HTTP probe `{name}` failed — check app / fpm / DNS."
            )
        elif name == "hardcodes":
            recs.append(f"[{product_id}] Hardcode scan failed — remove secrets/absolute paths.")
        elif name == "repo_hygiene":
            recs.append(f"[{product_id}] Repo hygiene failed — MagicMock/TODO policy.")
        elif name == "coverage":
            recs.append(
                f"[{product_id}] Coverage thresholds failed — "
                f"`python3 scripts/check_module_coverage.py --run` "
                f"or `tools/bin/lint_and_test.sh --coverage`; adjust "
                f"config/coverage_config.json fail_under/modules."
            )
        else:
            recs.append(
                f"[{product_id}] Investigate failed gate `{name}` (exit {r.get('exit')})."
            )

    for m in matrix_missing:
        recs.append(f"[{product_id}] Add or restore test path: `{m}`")

    recs.append(
        "**Human hard-stop:** do not `/release_mgmt` or push unreviewed fixes from night_shift."
    )
    return recs


def build_report_md(
    *,
    when: datetime,
    results: list[dict[str, Any]],
    recs: list[str],
    mode: str,
    product_id: str,
) -> str:
    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    overall = "PASS" if passed == total else "FAIL"
    lines = [
        f"# Night shift readiness — {product_id} — {when.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"**Overall:** {overall} ({passed}/{total} gates) · mode=`{mode}` · product=`{product_id}`",
        f"**Repo:** `{ROOT}`",
        "**Hard-stops:** no release, no push, no product auto-fix",
        "**SoT:** agent-harness `scripts/night_shift_readiness.py`",
        "",
        "## Gates",
        "",
        "| Gate | Result | Exit |",
        "|------|--------|------|",
    ]
    for r in results:
        tag = "✅" if r["ok"] else "❌"
        lines.append(f"| {r['name']} | {tag} | {r.get('exit')} |")
    lines.extend(["", "## Failures (tails)", ""])
    fails = [r for r in results if not r["ok"]]
    if not fails:
        lines.append("_None._")
    else:
        for r in fails:
            lines.append(f"### {r['name']}")
            lines.append("```")
            lines.append((r.get("stderr_tail") or r.get("stdout_tail") or "")[:1200])
            lines.append("```")
            lines.append("")
    lines.extend(["", "## Recommendations", ""])
    for i, rec in enumerate(recs, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")
    return "\n".join(lines)


def build_todo_md(
    *,
    when: datetime,
    overall: str,
    recs: list[str],
    results: list[dict[str, Any]],
    product_id: str,
) -> str:
    lines = [
        f"# {product_id} TODO (night_shift readiness)",
        "",
        f"_Auto-updated by harness `night_shift_readiness.py` at "
        f"{when.strftime('%Y-%m-%d %H:%M UTC')}. Overall: **{overall}**._",
        "",
        "Do **not** hand-edit the auto section; add notes under **Human backlog**.",
        "",
        "## Auto recommendations (from last night shift)",
        "",
    ]
    for rec in recs:
        lines.append(f"- [ ] {rec}")
    lines.extend(["", "## Last gate snapshot", ""])
    for r in results:
        box = "[x]" if r["ok"] else "[ ]"
        lines.append(f"- {box} `{r['name']}` (exit {r.get('exit')})")
    lines.extend(
        [
            "",
            "## Human backlog",
            "",
            "- [ ] ",
            "",
        ]
    )
    return "\n".join(lines)


def _gate_summary(results: list[dict[str, Any]]) -> str:
    passed = sum(1 for r in results if r.get("ok"))
    total = len(results)
    names = ",".join(r.get("name", "?") for r in results if r.get("ok"))
    if len(names) > 120:
        names = names[:117] + "..."
    return f"{passed}/{total}" + (f" {names}" if names else "")


def upsert_kanban_readiness_done(
    text: str,
    *,
    product_id: str,
    overall: str,
    when_iso: str,
    gate_summary: str,
) -> tuple[str, str]:
    """Insert or refresh a Done card for night_shift PASS. Pure (no I/O).

    Returns (new_text, message). Unchanged text when overall != PASS.
    """
    if overall != "PASS":
        return text, "kanban: skip (not PASS)"

    day = when_iso[:10] if when_iso else _now().strftime("%Y-%m-%d")
    card_id = f"T-NS-{product_id}-{day.replace('-', '')}"
    # Stable product-scoped id without date for single refreshable card
    stable_title = f"Night shift readiness PASS ({product_id})"
    notes_line = (
        f"  - notes: {KANBAN_AUTO_MARKER} @ {when_iso} · {gate_summary} · "
        f"see `01-Projects/{product_id}/TODO.md`"
    )
    card_body = (
        f"- [x] **{card_id}** — {stable_title} ({day})\n"
        f"{notes_line}\n"
        f"  - links: `01-Projects/{product_id}/TODO.md` | "
        f"`01-Projects/{product_id}/night-shift-log.md` | skill `night_shift`\n"
    )

    # Refresh existing auto card (any id) by marker in notes
    if KANBAN_AUTO_MARKER in text:
        # Replace from list item containing marker back to previous list item or section
        pattern = re.compile(
            r"- \[[ xX]\] \*\*T-[^*]+\*\* — [^\n]*\n"
            r"(?:  - [^\n]*\n)*?"
            rf"  - notes: {re.escape(KANBAN_AUTO_MARKER)}[^\n]*\n"
            r"(?:  - [^\n]*\n)*",
            re.MULTILINE,
        )
        if pattern.search(text):
            new_text = pattern.sub(card_body, text, count=1)
            return new_text, "kanban: refresh readiness Done note"
        # Marker present but odd shape — fall through to insert

    # Insert under ## Done (after heading / comment block)
    done_m = re.search(r"(## Done\n(?:<!--[^\n]*-->\n)?\n?)", text)
    if done_m:
        insert_at = done_m.end()
        new_text = text[:insert_at] + card_body + "\n" + text[insert_at:]
        return new_text, "kanban: insert readiness Done note"
    # No Done section — append
    new_text = text.rstrip() + "\n\n## Done\n\n" + card_body
    return new_text, "kanban: append Done section + readiness note"


def sync_kanban_readiness_file(
    vault: Path,
    *,
    product_id: str,
    overall: str,
    when: datetime,
    results: list[dict[str, Any]],
    dry_run: bool,
) -> str:
    """Write PASS readiness into vault agent-tasks/kanban.md Done note."""
    kanban = vault / "agent-tasks" / "kanban.md"
    if overall != "PASS":
        return "kanban: skip (not PASS)"
    if dry_run:
        return f"kanban: dry-run would upsert {kanban}"
    if not kanban.is_file():
        return f"kanban: skip (missing {kanban})"
    try:
        original = kanban.read_text(encoding="utf-8")
    except OSError as exc:
        return f"kanban: skip (read {exc})"
    when_iso = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    new_text, msg = upsert_kanban_readiness_done(
        original,
        product_id=product_id,
        overall=overall,
        when_iso=when_iso,
        gate_summary=_gate_summary(results),
    )
    if new_text == original:
        return msg
    try:
        kanban.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        return f"kanban: skip (write {exc})"
    return f"{msg} → {kanban}"


def write_vault(
    vault: Path,
    project_rel: Path,
    *,
    report_md: str,
    todo_md: str,
    when: datetime,
    overall: str,
    product_id: str,
    dry_run: bool,
    results: list[dict[str, Any]] | None = None,
) -> list[str]:
    notes: list[str] = []
    if dry_run:
        return ["vault: dry-run skip"]
    if not vault.is_dir():
        return [f"⚠️ VAULT SKIP: {vault} not found"]

    proj = vault / project_rel
    try:
        proj.mkdir(parents=True, exist_ok=True)
        log_path = proj / "night-shift-log.md"
        if not log_path.is_file():
            log_path.write_text(
                f"# {product_id} night-shift log\n\n"
                "Append-only readiness reports from `/night_shift` (harness SoT).\n\n",
                encoding="utf-8",
            )
        with log_path.open("a", encoding="utf-8") as f:
            f.write("\n---\n\n")
            f.write(report_md)
            if not report_md.endswith("\n"):
                f.write("\n")
        notes.append(f"vault log: {log_path}")

        todo_path = proj / "TODO.md"
        todo_path.write_text(todo_md, encoding="utf-8")
        notes.append(f"vault TODO: {todo_path}")

        notes.append(
            sync_kanban_readiness_file(
                vault,
                product_id=product_id,
                overall=overall,
                when=when,
                results=results or [],
                dry_run=dry_run,
            )
        )

        devlog = SCRIPTS / "sync_vault_devlog.py"
        if devlog.is_file():
            cmd = [
                sys.executable,
                str(devlog),
                "--vault",
                str(vault),
                "--note",
                f"Night shift readiness {product_id} {when.strftime('%Y-%m-%d')} {overall}",
                "--bullet",
                f"Overall: {overall}",
                "--bullet",
                f"Report: {project_rel}/night-shift-log.md",
                "--bullet",
                f"TODO: {project_rel}/TODO.md",
            ]
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
            notes.append((r.stdout or r.stderr or "devlog").strip())
    except PermissionError as exc:
        notes.append(f"⚠️ VAULT SKIP: {exc}")
    return notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--skip-live", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Product root (default: parent of scripts/)",
    )
    args = ap.parse_args(argv)

    global ROOT, SCRIPTS, ARTIFACTS
    if args.root is not None:
        ROOT = args.root.resolve()
        SCRIPTS = ROOT / "scripts"
        ARTIFACTS = ROOT / ".agents" / "artifacts"

    plugin = _load_plugin(ROOT)
    product_id = str(plugin.get("product_id") or ROOT.name)
    if product_id in ("product", "my-product", "example-api", "example"):
        product_id = ROOT.name
    when = _now()
    mode = "quick" if args.quick else ("full-no-live" if args.skip_live else "full")
    results = run_gates(quick=args.quick, skip_live=args.skip_live, plugin=plugin)

    matrix_missing: list[str] = []
    matrix_path = ROOT / ".agents" / "policy" / "TEST_MATRIX.md"
    checker = SCRIPTS / "check_test_matrix.py"
    if matrix_path.is_file() and checker.is_file():
        sys.path.insert(0, str(SCRIPTS))
        try:
            from check_test_matrix import check_matrix  # type: ignore

            _, matrix_rows = check_matrix(ROOT, matrix_path)
            for row in matrix_rows:
                matrix_missing.extend(row.get("missing") or [])
        except Exception as exc:  # noqa: BLE001
            matrix_missing.append(f"(matrix checker error: {exc})")

    recs = recommendations_from(results, matrix_missing, product_id)
    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    overall = "PASS" if passed == total else "FAIL"
    report_md = build_report_md(
        when=when,
        results=results,
        recs=recs,
        mode=mode,
        product_id=product_id,
    )
    todo_md = build_todo_md(
        when=when,
        overall=overall,
        recs=recs,
        results=results,
        product_id=product_id,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "product_id": product_id,
                    "overall": overall,
                    "passed": passed,
                    "total": total,
                    "results": [
                        {"name": r["name"], "ok": r["ok"], "exit": r["exit"]}
                        for r in results
                    ],
                    "recommendations": recs,
                },
                indent=2,
            )
        )

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if not args.dry_run:
        (ARTIFACTS / "NIGHT_SHIFT_REPORT.md").write_text(report_md, encoding="utf-8")
        (ARTIFACTS / "NIGHT_SHIFT_TODO.md").write_text(todo_md, encoding="utf-8")
        print(f"artifact: {ARTIFACTS / 'NIGHT_SHIFT_REPORT.md'}")
        print(f"artifact: {ARTIFACTS / 'NIGHT_SHIFT_TODO.md'}")
    else:
        print(report_md)

    vault = _vault_root(plugin, args.vault)
    project_rel = _vault_project_rel(plugin)
    for n in write_vault(
        vault.expanduser().resolve() if isinstance(vault, Path) else Path(vault),
        project_rel,
        report_md=report_md,
        todo_md=todo_md,
        when=when,
        overall=overall,
        product_id=product_id,
        dry_run=args.dry_run,
        results=results,
    ):
        print(n)

    print(
        f"{'✅' if overall == 'PASS' else '❌'} night_shift readiness "
        f"{product_id} {overall} ({passed}/{total})"
    )
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

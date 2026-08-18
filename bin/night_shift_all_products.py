#!/usr/bin/env python3
"""Run night_shift readiness across all registered product repos (harness SoT).

Schedule: 03:15 Asia/Hong_Kong via agent-harness systemd timer.

Config (first found wins):
  1. $NIGHT_SHIFT_PRODUCTS_FILE
  2. <harness>/config/night_shift_products.yaml
  3. Built-in defaults under $HOME/*

Writes multi-product summary:
  - vault agent-tasks/night-shift/SUMMARY.md (latest)
  - vault agent-tasks/night-shift/log.md (append)
  - <harness>/.agents/artifacts/NIGHT_SHIFT_ALL_REPORT.md
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path


def _vw(path: Path, text: str) -> None:
    try:
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        sys.path.insert(0, str(scripts))
        from vault_fs import write_text as _w  # type: ignore
        _w(path, text)
    except Exception:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")



def format_when_dual(when: datetime | None = None) -> str:
    when = when or datetime.now(UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    else:
        when = when.astimezone(UTC)
    utc_s = when.strftime("%Y-%m-%d %H:%M UTC")
    try:
        from zoneinfo import ZoneInfo
        hkt_s = when.astimezone(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M HKT")
    except Exception:
        hkt_s = when.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M HKT")
    return f"{utc_s} · {hkt_s}"

HARNESS_ROOT = Path(__file__).resolve().parent.parent
# Prefer env; fall back next to harness sibling dirs under $HOME (no /home/<user> literals).
_HOME = Path.home()
DEFAULT_VAULT = Path(os.environ["PRODUCT_VAULT_ROOT"]) if os.environ.get("PRODUCT_VAULT_ROOT") else Path("")
DEFAULT_PRODUCTS = [
    ("watchlist", _HOME / "watchlist"),
    ("email-detach", _HOME / "email-detach"),
    ("substack-push", _HOME / "substack-push"),
    ("second-brain", _HOME / "second-brain"),
    ("catalyxt", _HOME / "catalyxt-website"),
    ("agent-harness", HARNESS_ROOT),
    ("ocr-ledger", _HOME / "ocr-ledger"),
]


def _load_products(path: Path | None) -> list[tuple[str, Path]]:
    if path is None:
        env = os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE")
        path = Path(env) if env else HARNESS_ROOT / "config" / "night_shift_products.yaml"
    if not path.is_file():
        return [(n, p) for n, p in DEFAULT_PRODUCTS if p.is_dir()]
    rows: list[tuple[str, Path]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # id: path  or  - id: path
        line = line.lstrip("-").strip()
        if ":" not in line:
            continue
        pid, proot = line.split(":", 1)
        pid = pid.strip()
        proot_p = Path(proot.strip().strip("\"'")).expanduser()
        if proot_p.is_dir():
            rows.append((pid, proot_p))
    return rows or [(n, p) for n, p in DEFAULT_PRODUCTS if p.is_dir()]


def _product_python(root: Path) -> str:
    """Prefer product virtualenv so gates (e.g. pydantic) resolve correctly.

    Uses ``product_venv.product_venv_python`` (absolute, not resolve) so Unix
    venv symlinks keep site-packages. Windows prefers Scripts\\python.exe.
    """
    helper = HARNESS_ROOT / "scripts" / "product_venv.py"
    if helper.is_file():
        import importlib.util

        spec = importlib.util.spec_from_file_location("product_venv", helper)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            vpy = mod.product_venv_python(root)
            if vpy is not None:
                return str(vpy)
    for rel in (
        ".venv/bin/python",
        "venv/bin/python",
        ".venv/bin/python3",
        "venv/bin/python3",
        ".venv/Scripts/python.exe",
        "venv/Scripts/python.exe",
    ):
        p = root / rel
        if p.is_file() and (os.access(p, os.X_OK) or str(p).lower().endswith(".exe")):
            return str(p.absolute())
    return sys.executable


def _preflight_dev_env(root: Path, *, dry_run: bool) -> dict:
    """Ensure product .venv + requirements-dev when present (no sudo pip)."""
    helper = HARNESS_ROOT / "scripts" / "ensure_product_dev_env.py"
    if not helper.is_file():
        # Product install may carry a copy under scripts/
        helper = root / "scripts" / "ensure_product_dev_env.py"
    if not helper.is_file():
        return {
            "ok": True,
            "status": "skip",
            "message": "ensure_product_dev_env.py missing",
            "python": _product_python(root),
        }
    # Import by path so harness SoT works without install
    import importlib.util

    spec = importlib.util.spec_from_file_location("ensure_product_dev_env", helper)
    if not spec or not spec.loader:
        return {
            "ok": False,
            "status": "fail",
            "message": "cannot load ensure_product_dev_env",
            "python": _product_python(root),
        }
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ensure_product_dev_env(root, dry_run=dry_run)


def run_one(
    name: str,
    root: Path,
    *,
    vault: Path,
    quick: bool,
    skip_live: bool,
    dry_run: bool,
) -> dict:
    pre = _preflight_dev_env(root, dry_run=dry_run)
    if not pre.get("ok"):
        return {
            "name": name,
            "root": str(root),
            "exit": 1,
            "ok": False,
            "tail": f"preflight FAIL: {pre.get('status')}: {pre.get('message')}",
            "preflight": pre,
        }

    script = root / "scripts" / "night_shift_readiness.py"
    py = pre.get("python") or _product_python(root)
    # Prefer product copy; fall back to harness SoT with --root
    if script.is_file():
        cmd = [py, str(script), "--vault", str(vault)]
        cwd = root
    else:
        sot = HARNESS_ROOT / "scripts" / "night_shift_readiness.py"
        cmd = [py, str(sot), "--root", str(root), "--vault", str(vault)]
        cwd = root
    if quick:
        cmd.append("--quick")
    if skip_live:
        cmd.append("--skip-live")
    if dry_run:
        cmd.append("--dry-run")

    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=3600,
            env={
                **os.environ,
                "PRODUCT_VAULT_ROOT": str(vault),
                "WATCHLIST_VAULT_ROOT": str(vault),
            },
        )
        out = (r.stdout or "") + (r.stderr or "")
        return {
            "name": name,
            "root": str(root),
            "exit": r.returncode,
            "ok": r.returncode == 0,
            "tail": out[-2000:],
            "preflight": pre,
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "root": str(root),
            "exit": 124,
            "ok": False,
            "tail": "timeout 3600s",
            "preflight": pre,
        }
    except Exception as exc:
        return {
            "name": name,
            "root": str(root),
            "exit": 1,
            "ok": False,
            "tail": str(exc),
            "preflight": pre,
        }


def write_summary(vault: Path, when: datetime, rows: list[dict], dry_run: bool) -> list[str]:
    notes: list[str] = []
    passed = sum(1 for r in rows if r["ok"])
    total = len(rows)
    overall = "PASS" if passed == total else "FAIL"
    lines = [
        f"# Multi-product night shift — {format_when_dual(when)}",
        "",
        f"**Overall:** {overall} ({passed}/{total} products)",
        "**Schedule:** 03:15 Asia/Hong_Kong (harness timer)",
        f"**SoT:** `{HARNESS_ROOT}`",
        "",
        "| Product | Result | Exit | Root |",
        "|---------|--------|------|------|",
    ]
    for r in rows:
        tag = "✅" if r["ok"] else "❌"
        lines.append(f"| {r['name']} | {tag} | {r['exit']} | `{r['root']}` |")
    lines.extend(["", "## Per-product failures (tails)", ""])
    fails = [r for r in rows if not r["ok"]]
    if not fails:
        lines.append("_All products green._")
    else:
        for r in fails:
            lines.append(f"### {r['name']}")
            lines.append("```")
            lines.append(r.get("tail") or "")
            lines.append("```")
            lines.append("")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "1. Open each product vault `01-Projects/<label>/TODO.md` for checkboxes.",
            "2. Fix failed products before `/execute_dev` on that repo.",
            "3. **Hard-stop:** no multi-repo auto-release from this job.",
            "",
        ]
    )
    body = "\n".join(lines)

    art = HARNESS_ROOT / ".agents" / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        (art / "NIGHT_SHIFT_ALL_REPORT.md").write_text(body, encoding="utf-8")
        notes.append(f"artifact: {art / 'NIGHT_SHIFT_ALL_REPORT.md'}")

    if dry_run:
        print(body)
        return notes

    if not vault.is_dir():
        notes.append(f"⚠️ VAULT SKIP: {vault}")
        return notes

    proj = vault / "agent-tasks" / "night-shift"
    try:
        proj.mkdir(parents=True, exist_ok=True)
        _vw(proj / "SUMMARY.md", body)
        notes.append(f"vault summary: {proj / 'SUMMARY.md'}")
        log = proj / "log.md"  # multi orchestrator log (newest first)
        header = (
            "# Multi-product night-shift log\n\n"
            "Newest-first multi-product runs (harness SoT). Times: **UTC · HKT**.\n\n"
        )
        chunk = body.rstrip() + "\n\n---\n\n"
        if not log.is_file():
            _vw(log, header + chunk)
        else:
            existing = log.read_text(encoding="utf-8", errors="replace")
            marker = "# Multi-product night shift —"
            idx = existing.find(marker)
            bodies = existing[idx:] if idx >= 0 else existing
            _vw(log, header + chunk + bodies.lstrip())
        notes.append(f"vault log: {log}")
        # cross-product TODO
        todo_lines = [
            "# All products TODO (night_shift multi)",
            "",
            f"_Updated **{format_when_dual(when)}** · **{overall}** ({passed}/{total})_",
            "",
            "## Products",
            "",
        ]
        for r in rows:
            box = "[x]" if r["ok"] else "[ ]"
            todo_lines.append(f"- {box} **{r['name']}** — see `01-Projects/{r['name']}/TODO.md`")
        todo_lines.extend(
            [
                "",
                "## Actions",
                "",
            ]
        )
        if fails:
            for r in fails:
                todo_lines.append(
                    f"- [ ] Fix readiness on **{r['name']}** (exit {r['exit']})"
                )
        else:
            todo_lines.append(
                "- [ ] All green — pick next product work from each roadmap Shaping section"
            )
        todo_lines.append("")
        _vw(proj / "TODO.md", "\n".join(todo_lines) + "\n")
        notes.append(f"vault TODO: {proj / 'TODO.md'}")
    except PermissionError as exc:
        notes.append(f"⚠️ VAULT SKIP: {exc}")
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=Path(os.environ.get("PRODUCT_VAULT_ROOT") or os.environ.get("WATCHLIST_VAULT_ROOT") or str(DEFAULT_VAULT)),
    )
    ap.add_argument("--products-file", type=Path, default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--skip-live", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run only this product id (repeatable)",
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="Parallel product workers (default: min(product count, 10); 1 = sequential)",
    )
    args = ap.parse_args()

    products = _load_products(args.products_file)
    if args.only:
        allow = set(args.only)
        products = [(n, p) for n, p in products if n in allow]

    when = datetime.now(UTC)
    n_prod = len(products)
    jobs = args.jobs if args.jobs > 0 else min(n_prod, 10)
    jobs = max(1, min(jobs, n_prod or 1))
    print(
        f"night_shift_all: {n_prod} product(s) jobs={jobs} @ {when.isoformat()}"
    )

    # Path contract P0/P1: fleet paths + consumers (fail closed for multi-product run)
    path_gate_failed = False
    for gate_name, gate_rel in (
        ("night_shift_product_paths", "scripts/check_night_shift_product_paths.py"),
        ("product_path_consumers", "scripts/check_product_path_consumers.py"),
    ):
        gate = HARNESS_ROOT / gate_rel
        if not gate.is_file():
            continue
        gcmd = [sys.executable, str(gate)]
        if args.products_file:
            gcmd.extend(["--products-file", str(args.products_file)])
        print(f"--- harness gate: {gate_name} ---")
        if args.dry_run:
            print(f"   dry-run: would run {gate}")
            continue
        grc = subprocess.run(gcmd, cwd=str(HARNESS_ROOT), check=False).returncode
        print(f"{'✅' if grc == 0 else '❌'} {gate_name} exit={grc}")
        if grc != 0:
            path_gate_failed = True

    vault_resolved = args.vault.expanduser().resolve()
    wall0 = time.perf_counter()
    try:
        import resource

        def _cpu_s() -> float:
            self_u = resource.getrusage(resource.RUSAGE_SELF)
            ch_u = resource.getrusage(resource.RUSAGE_CHILDREN)
            return (
                self_u.ru_utime
                + self_u.ru_stime
                + ch_u.ru_utime
                + ch_u.ru_stime
            )

        cpu0 = _cpu_s()
    except Exception:  # noqa: BLE001

        def _cpu_s() -> float:
            return time.process_time()

        cpu0 = _cpu_s()

    def _job(item: tuple[str, Path]) -> dict:
        name, root = item
        print(f"--- start {name} ({root}) ---", flush=True)
        row = run_one(
            name,
            root,
            vault=vault_resolved,
            quick=args.quick,
            skip_live=args.skip_live,
            dry_run=args.dry_run,
        )
        pf = row.get("preflight") or {}
        if pf:
            print(
                f"   {name} preflight: {pf.get('status')}: "
                f"{str(pf.get('message', ''))[:120]}",
                flush=True,
            )
        print(
            f"{'✅' if row['ok'] else '❌'} {name} exit={row['exit']}",
            flush=True,
        )
        return row

    # Preserve config order in summary regardless of completion order
    rows: list[dict] = []
    if jobs == 1 or n_prod <= 1:
        for item in products:
            rows.append(_job(item))
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futs = {pool.submit(_job, item): item[0] for item in products}
            by_name: dict[str, dict] = {}
            for fut in as_completed(futs):
                row = fut.result()
                by_name[str(row["name"])] = row
            rows = [by_name[n] for n, _ in products if n in by_name]

    wall_s = time.perf_counter() - wall0
    cpu_s = max(0.0, _cpu_s() - cpu0)
    print(
        f"night_shift_all timing: wall={wall_s:.1f}s "
        f"cpu_self+children={cpu_s:.1f}s "
        f"jobs={jobs} products={n_prod} "
        f"(parallel: wall→~slowest product, not sum)"
    )

    for n in write_summary(vault_resolved, when, rows, args.dry_run):
        print(n)

    passed = sum(1 for r in rows if r["ok"])
    total = len(rows)
    overall = "PASS" if passed == total and not path_gate_failed else "FAIL"
    print(f"{'✅' if overall == 'PASS' else '❌'} night_shift_all {overall} ({passed}/{total})")
    if path_gate_failed:
        print("❌ harness path contract gate(s) failed (product paths / consumers)")

    vault_path = args.vault.expanduser().resolve()

    # Rotate vault FAIL spam when latest is PASS; rebuild SUMMARY
    try:
        rot = HARNESS_ROOT / "scripts" / "rotate_night_shift_logs.py"
        if rot.is_file() and not args.dry_run:
            subprocess.run(
                [sys.executable, str(rot), "--vault", str(vault_path)],
                cwd=str(HARNESS_ROOT),
                check=False,
            )
    except Exception as exc:
        print(f"⚠️ rotate_night_shift_logs: {exc}")

    # --- Dev-log anti-drift (all 01-Projects/*/dev-log.md, no product exceptions) ---
    # 1) Normalize (newest-first + When/Kind backfill)
    # 2) Contract check — fail multi-product run if anything still drifts
    contract_rc = 0
    if not args.dry_run:
        norm = HARNESS_ROOT / "scripts" / "normalize_vault_devlog.py"
        check = HARNESS_ROOT / "scripts" / "check_dev_log_contract.py"
        if norm.is_file():
            print("--- normalize_vault_devlog (all projects) ---")
            r = subprocess.run(
                [sys.executable, str(norm), "--vault", str(vault_path)],
                cwd=str(HARNESS_ROOT),
                check=False,
            )
            if r.returncode != 0:
                print(f"⚠️ normalize_vault_devlog exit={r.returncode}")
                contract_rc = 1
        else:
            print("⚠️ normalize_vault_devlog.py missing")
            contract_rc = 1
        if check.is_file():
            print("--- check_dev_log_contract ---")
            r = subprocess.run(
                [sys.executable, str(check), "--vault", str(vault_path)],
                cwd=str(HARNESS_ROOT),
                check=False,
            )
            if r.returncode != 0 and norm.is_file():
                # Second normalize pass (mojibake headings / mid-file inserts)
                print("--- normalize_vault_devlog (retry after contract fail) ---")
                subprocess.run(
                    [sys.executable, str(norm), "--vault", str(vault_path)],
                    cwd=str(HARNESS_ROOT),
                    check=False,
                )
                print("--- check_dev_log_contract (retry) ---")
                r = subprocess.run(
                    [sys.executable, str(check), "--vault", str(vault_path)],
                    cwd=str(HARNESS_ROOT),
                    check=False,
                )
            if r.returncode != 0:
                contract_rc = 1
        else:
            print("⚠️ check_dev_log_contract.py missing")
            contract_rc = 1
    else:
        print("dev-log normalize/check: dry-run skip")

    if contract_rc != 0:
        print(
            "❌ night_shift_all FAIL (dev-log contract drift after normalize+retry). "
            "Inspect 01-Projects/*/dev-log.md; fix headings then re-run normalize."
        )
        return 1

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

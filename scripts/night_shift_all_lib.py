#!/usr/bin/env python3
"""Night-shift multi-product engine (library).

The CLI at ``bin/night_shift_all_products.py`` is deliberately thin: argparse,
``main``, and the two test seams (``run_one`` / ``collect_and_learn``). All
product discovery, interpreter/port resolution, gate execution, summary
writing, and post-run maintenance live here so the CLI stays reviewable
(~E07: <=400 lines after the split).

Schedule: 03:15 Asia/Hong_Kong via the agent-harness systemd timer.
"""
from __future__ import annotations

import argparse
import contextlib
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

fcntl: Any
try:  # POSIX cross-process port locks; Windows falls back to in-process locks
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


def _vw(path: Path, text: str) -> None:
    try:
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        sys.path.insert(0, str(scripts))
        from vault_fs import write_text as _w
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
CANONICAL_VAULT = Path("/opt/second-brain/vault")


def resolve_night_vault(vault: Path | None) -> tuple[Path | None, str]:
    """Return (vault, "") or (None, reason). Never write into the harness checkout."""
    raw = "" if vault is None else str(vault).strip()
    chosen = CANONICAL_VAULT if raw in ("", ".") else Path(raw)
    resolved = chosen.expanduser().resolve()
    harness = HARNESS_ROOT.resolve()
    if resolved == harness or harness in resolved.parents:
        return None, (
            f"REFUSING: vault {resolved} is inside the harness checkout {harness}. "
            "Set PRODUCT_VAULT_ROOT=/opt/second-brain/vault"
        )
    if not resolved.is_dir():
        return None, f"REFUSING: vault {resolved} is not a directory"
    return resolved, ""
DEFAULT_PRODUCTS = [
    ("watchlist", _HOME / "watchlist"),
    ("email-detach", _HOME / "email-detach"),
    ("substack-push", _HOME / "substack-push"),
    ("second-brain", _HOME / "second-brain"),
    ("catalyxt", _HOME / "catalyxt-website"),
    ("agent-harness", HARNESS_ROOT),
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


RUNTIME_DEFAULT: dict[str, Any] = {
    "python": "venv",
    "port": None,
    "binds": [],
    "port_env": [],
}
PYTHON_POLICIES = ("venv", "harness")
EXIT_INTERPRETER_MISSING = 3
EXIT_PORT_LOCK_TIMEOUT = 125
PORT_LOCK_TIMEOUT_S = int(os.environ.get("NIGHT_SHIFT_PORT_LOCK_TIMEOUT", "5400"))
# jobs=10 on 2026-11-01 left nine products past this wall (exit 124) while CPU
# stayed ~10 min. Default workers stay at 2 so the timer unit, which passes no
# --jobs, does not stampede. Override with NIGHT_SHIFT_JOBS or --jobs.
DEFAULT_JOBS = int(os.environ.get("NIGHT_SHIFT_JOBS", "2"))
# 3600 was shorter than validate_full + product_smoke + coverage on this host
# (2026-11-01 agent-harness alone still exit 124). 7200 covers that sum.
PRODUCT_TIMEOUT_S = int(os.environ.get("NIGHT_SHIFT_PRODUCT_TIMEOUT", "7200"))


def default_jobs() -> int:
    """Workers for this run; read at call time so env changes are honored."""
    return max(1, int(os.environ.get("NIGHT_SHIFT_JOBS", "2")))


def product_timeout_s() -> int:
    return int(os.environ.get("NIGHT_SHIFT_PRODUCT_TIMEOUT", "7200"))


def _load_runtime(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Parse ``config/night_shift_runtime.yaml`` (``id: key=value ...`` lines).

    Raises ValueError on unknown keys / bad values (fail loud, never guess).
    """
    if path is None:
        env = os.environ.get("NIGHT_SHIFT_RUNTIME_FILE")
        path = Path(env) if env else HARNESS_ROOT / "config" / "night_shift_runtime.yaml"
    out: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return out
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        line = line.lstrip("-").strip()
        pid, rest = line.split(":", 1)
        pid = pid.strip()
        cfg: dict[str, Any] = {k: (list(v) if isinstance(v, list) else v) for k, v in RUNTIME_DEFAULT.items()}
        for tok in rest.split():
            if "=" not in tok:
                raise ValueError(f"{path}:{lineno}: {pid}: expected key=value, got {tok!r}")
            key, val = tok.split("=", 1)
            try:
                if key == "python":
                    if val not in PYTHON_POLICIES:
                        raise ValueError(f"python must be one of {PYTHON_POLICIES}")
                    cfg["python"] = val
                elif key == "port":
                    cfg["port"] = int(val)
                elif key == "binds":
                    cfg["binds"] = [int(x) for x in val.split(",") if x.strip()]
                elif key == "port_env":
                    cfg["port_env"] = [x.strip() for x in val.split(",") if x.strip()]
                else:
                    raise ValueError(f"unknown key {key!r}")
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: {pid}: {exc}") from exc
        out[pid] = cfg
    return out


def runtime_for(name: str, runtime: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cfg = runtime.get(name)
    if cfg is None:
        return {k: (list(v) if isinstance(v, list) else v) for k, v in RUNTIME_DEFAULT.items()}
    return cfg


def product_lock_ports(cfg: dict[str, Any]) -> list[int]:
    ports = set(cfg.get("binds") or [])
    if cfg.get("port") is not None:
        ports.add(int(cfg["port"]))
    return sorted(ports)


def check_port_map(
    products: list[tuple[str, Path]], runtime: dict[str, dict[str, Any]]
) -> tuple[list[str], dict[int, list[str]]]:
    """Return (errors, shared) — errors: duplicate *assigned* ports (fatal);
    shared: port -> products that will contend for it (serialized by lock)."""
    errors: list[str] = []
    assigned: dict[int, str] = {}
    contenders: dict[int, list[str]] = {}
    for name, _ in products:
        cfg = runtime_for(name, runtime)
        port = cfg.get("port")
        if port is not None:
            if port in assigned:
                errors.append(f"port {port} assigned to both {assigned[port]} and {name}")
            else:
                assigned[port] = name
        for p in product_lock_ports(cfg):
            contenders.setdefault(p, []).append(name)
    shared = {p: names for p, names in sorted(contenders.items()) if len(names) > 1}
    return errors, shared


def _product_venv(root: Path) -> str | None:
    """Product venv interpreter (absolute, symlinks kept) or None. No fallback."""
    helper = HARNESS_ROOT / "scripts" / "product_venv.py"
    if helper.is_file():
        import importlib.util

        spec = importlib.util.spec_from_file_location("product_venv", helper)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            vpy = mod.product_venv_python(root)
            return str(vpy) if vpy is not None else None
    for rel in (".venv/bin/python", ".venv/bin/python3", "venv/bin/python", "venv/bin/python3"):
        p = root / rel
        if p.is_file() and os.access(p, os.X_OK):
            return str(p.absolute())
    return None


def resolve_product_python(
    name: str, root: Path, runtime: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Per-product interpreter. Order: product venv -> explicit python=harness -> FAIL.

    Returns {ok, python, source, error}. Never silently returns the harness python.
    """
    cfg = runtime_for(name, runtime)
    vpy = _product_venv(root)
    if vpy:
        return {"ok": True, "python": vpy, "source": "product-venv", "error": ""}
    if cfg.get("python") == "harness":
        return {
            "ok": True,
            "python": sys.executable,
            "source": "harness-fallback (explicit python=harness; product has no venv)",
            "error": "",
        }
    return {
        "ok": False,
        "python": None,
        "source": "missing",
        "error": (
            f"INTERPRETER FAIL: {name}: product venv missing under {root} "
            "(looked for .venv/bin/python[3], venv/bin/python[3]). Refusing to run "
            f"product gates with the harness interpreter {sys.executable}. Fix: "
            f"python3 -m venv {root}/.venv && {root}/.venv/bin/pip install -r "
            f"{root}/requirements-dev.txt — or, for a product with no Python deps, "
            f"declare '{name}: python=harness' in config/night_shift_runtime.yaml."
        ),
    }


def product_env(
    name: str, interp: dict[str, Any], cfg: dict[str, Any], base: dict[str, str] | None = None
) -> dict[str, str]:
    """Child env: product venv first on PATH + assigned port vars."""
    env = dict(os.environ if base is None else base)
    py = str(interp.get("python") or "")
    env["NIGHT_SHIFT_PRODUCT_ID"] = name
    env["NIGHT_SHIFT_PRODUCT_PYTHON"] = py
    if interp.get("source") == "product-venv" and py:
        venv_bin = Path(py).parent
        env["VIRTUAL_ENV"] = str(venv_bin.parent)
        env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")
        env.pop("PYTHONHOME", None)
    port = cfg.get("port")
    if port is not None:
        for var in ("NIGHT_SHIFT_E2E_PORT", "PLAYWRIGHT_PORT", *(cfg.get("port_env") or [])):
            env[var] = str(port)
    return env


_THREAD_PORT_LOCKS: dict[int, threading.Lock] = {}
_THREAD_PORT_LOCKS_GUARD = threading.Lock()


def _lock_dir() -> Path:
    return Path(os.environ.get("NIGHT_SHIFT_LOCK_DIR") or tempfile.gettempdir())


@contextlib.contextmanager
def port_locks(
    name: str,
    ports: list[int],
    *,
    timeout_s: int = PORT_LOCK_TIMEOUT_S,
    poll_s: float = 1.0,
) -> Iterator[dict[str, Any]]:
    """Hold exclusive locks on ``ports`` (sorted order => no deadlock).

    Uses flock on ``<lockdir>/night-shift-port-<n>.lock`` so parallel workers
    *and* concurrent manual runs never share a port. Yields {wait_s, waited_on}.
    """
    held: list[Any] = []
    waited_on: list[str] = []
    t0 = time.monotonic()
    try:
        for port in sorted(set(ports)):
            if fcntl is None:  # pragma: no cover - Windows
                with _THREAD_PORT_LOCKS_GUARD:
                    lk = _THREAD_PORT_LOCKS.setdefault(port, threading.Lock())
                if not lk.acquire(timeout=timeout_s):
                    raise TimeoutError(f"port lock :{port} timeout after {timeout_s}s")
                held.append(lk)
                continue
            path = _lock_dir() / f"night-shift-port-{port}.lock"
            fh = open(path, "a+", encoding="utf-8")  # noqa: SIM115
            announced = False
            while True:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    holder = ""
                    try:
                        holder = path.read_text(encoding="utf-8").strip()
                    except OSError:
                        pass
                    if not announced:
                        print(
                            f"   {name}: waiting for port :{port} (held by {holder or '?'})",
                            flush=True,
                        )
                        waited_on.append(f":{port} held by {holder or '?'}")
                        announced = True
                    if time.monotonic() - t0 > timeout_s:
                        fh.close()
                        raise TimeoutError(
                            f"port lock :{port} timeout after {timeout_s}s (held by {holder or '?'})"
                        ) from None
                    time.sleep(poll_s)
            fh.seek(0)
            fh.truncate()
            fh.write(f"{name} pid={os.getpid()}\n")
            fh.flush()
            held.append(fh)
        yield {"wait_s": time.monotonic() - t0, "waited_on": waited_on}
    finally:
        for h in reversed(held):
            if not hasattr(h, "fileno"):  # in-process threading lock (no fcntl)
                try:
                    h.release()
                except RuntimeError:
                    pass
                continue
            try:
                if fcntl is not None:
                    fcntl.flock(h.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            h.close()


def build_plan(
    products: list[tuple[str, Path]], runtime: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Interpreter + port map per product (no gates run)."""
    plan: list[dict[str, Any]] = []
    for name, root in products:
        cfg = runtime_for(name, runtime)
        interp = resolve_product_python(name, root, runtime)
        plan.append(
            {
                "name": name,
                "root": str(root),
                "python": interp.get("python"),
                "source": interp.get("source"),
                "ok": interp.get("ok"),
                "error": interp.get("error"),
                "port": cfg.get("port"),
                "lock_ports": product_lock_ports(cfg),
            }
        )
    return plan


def port_listening(port: int, host: str = "127.0.0.1") -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def format_plan(plan: list[dict[str, Any]], shared: dict[int, list[str]]) -> str:
    lines = [
        "| Product | Python | Source | Assigned port | Locked ports | Listening now |",
        "|---------|--------|--------|---------------|--------------|---------------|",
    ]
    for p in plan:
        py = p["python"] or "**MISSING**"
        port = p["port"] if p["port"] is not None else "-"
        locks = ",".join(str(x) for x in p["lock_ports"]) or "-"
        busy = [str(x) for x in p["lock_ports"] if port_listening(x)]
        lines.append(
            f"| {p['name']} | `{py}` | {p['source']} | {port} | {locks} | "
            f"{','.join(busy) or '-'} |"
        )
    if shared:
        lines.append("")
        for port, names in shared.items():
            lines.append(
                f"- port :{port} contended by {', '.join(names)} → serialized by harness port lock"
            )
    return "\n".join(lines)


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


def _watchlist_golden_precheck(*, dry_run: bool) -> str:
    """Pre-night golden-drift check for the watchlist product (SoT: fixtures README).

    Runs the harness checker before readiness so SMA50/RSI/price fixtures are
    re-exported via `php bin/refresh.php --export-golden=TICKER` before the
    nightly ParityTest gate goes red. Weekly catch-up (Sundays UTC) also
    re-exports fixtures with <25% band headroom, just before they will breach.
    Non-gating: a checker failure is reported, readiness still decides.
    """
    checker = HARNESS_ROOT / "scripts" / "watchlist_golden_drift.py"
    if not checker.is_file():
        return "skip: watchlist_golden_drift.py missing from harness"
    cmd = [sys.executable, str(checker)]
    if not dry_run:
        cmd.append("--fix")
        if datetime.now(UTC).weekday() == 6:  # Sunday UTC: weekly headroom catch-up
            cmd.append("--weekly")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        tail = (r.stdout or "").strip().splitlines()
        keep = [ln for ln in tail if "BEYOND" in ln or "WOULD" in ln or "headroom" in ln
                or "re-export" in ln or "all fixtures" in ln or "FAIL" in ln]
        summary = " | ".join(keep[-6:]) or (tail[-1] if tail else "")
        return f"exit={r.returncode} {summary}"
    except Exception as exc:  # noqa: BLE001 — pre-step must never kill the night run
        return f"skip: {exc}"


def run_one(
    name: str,
    root: Path,
    *,
    vault: Path,
    quick: bool,
    skip_live: bool,
    dry_run: bool,
    runtime: dict[str, dict[str, Any]] | None = None,
) -> dict:
    if runtime is None:
        runtime = _load_runtime()
    cfg = runtime_for(name, runtime)
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

    # Per-product interpreter (Ops-430): resolved *after* preflight so a venv it
    # just created is used. Never fall back to harness python silently.
    interp = resolve_product_python(name, root, runtime)
    base_row: dict[str, Any] = {
        "name": name,
        "root": str(root),
        "preflight": pre,
        "python": interp.get("python"),
        "python_source": interp.get("source"),
        "port": cfg.get("port"),
        "lock_ports": product_lock_ports(cfg),
    }
    if not interp.get("ok"):
        print(f"❌ {interp['error']}", file=sys.stderr, flush=True)
        return {
            **base_row,
            "exit": EXIT_INTERPRETER_MISSING,
            "ok": False,
            "tail": interp["error"],
        }

    # Pre-night golden-drift check (watchlist only, T1905U): re-export stale
    # golden fixtures via the fixtures-README remedy BEFORE ParityTest runs.
    golden = ""
    if name == "watchlist" and (root / "tests" / "fixtures" / "golden").is_dir():
        golden = _watchlist_golden_precheck(dry_run=dry_run)
        base_row["golden_drift"] = golden
        print(f"[{name}] golden precheck: {golden}", file=sys.stderr, flush=True)

    # Always use harness SoT readiness so gate behavior (incl. vault_schema_lint
    # surface-alias fix) is not blocked on lagging per-product script ports.
    py = str(interp["python"])
    sot = HARNESS_ROOT / "scripts" / "night_shift_readiness.py"
    cmd = [py, str(sot), "--root", str(root), "--vault", str(vault)]
    cwd = root
    if quick:
        cmd.append("--quick")
    if skip_live:
        cmd.append("--skip-live")
    if dry_run:
        cmd.append("--dry-run")

    sot_lint = HARNESS_ROOT / "scripts" / "vault_schema_lint.py"
    env = product_env(name, interp, cfg)
    env.update(
        {
            "PRODUCT_VAULT_ROOT": str(vault),
            "WATCHLIST_VAULT_ROOT": str(vault),
            # Product validate.py still runs from product scripts/; skip its
            # possibly-stale vault_schema_lint and use harness SoT instead.
            "NIGHT_SHIFT_SOT_LINT": str(sot_lint) if sot_lint.is_file() else "",
        }
    )
    try:
        with port_locks(name, product_lock_ports(cfg)) as lk:
            base_row["lock_wait_s"] = round(lk["wait_s"], 1)
            base_row["lock_waited_on"] = lk["waited_on"]
            t_run = time.perf_counter()
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                start_new_session=True,
            )
            try:
                stdout, stderr = proc.communicate(timeout=product_timeout_s())
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                base_row["run_s"] = round(time.perf_counter() - t_run, 1)
                return {
                    **base_row,
                    "exit": 124,
                    "ok": False,
                    "tail": f"timeout {product_timeout_s()}s",
                }
            base_row["run_s"] = round(time.perf_counter() - t_run, 1)
        out = (stdout or "") + (stderr or "")
        return attach_fail_hints(
            {
                **base_row,
                "exit": proc.returncode,
                "ok": proc.returncode == 0,
                "tail": out[-2000:],
            },
            out,
        )
    except TimeoutError as exc:
        return {**base_row, "exit": EXIT_PORT_LOCK_TIMEOUT, "ok": False, "tail": str(exc)}
    except Exception as exc:
        return {**base_row, "exit": 1, "ok": False, "tail": str(exc)}


_FAIL_TABLE = re.compile(
    r"^\|\s*`?([A-Za-z0-9_]+)`?\s*\|\s*❌\s*\|\s*([^|]*)\|",
    re.MULTILINE,
)
_FAIL_HEADING = re.compile(r"^###\s+(\S+)\s*$")


def parse_fail_hints(text: str) -> list[dict[str, str]]:
    """One hint per ``Fix:`` line, in heading order. Does not invent gates."""
    exits: dict[str, str] = {}
    for match in _FAIL_TABLE.finditer(text or ""):
        exits[match.group(1)] = match.group(2).strip()
    hints: list[dict[str, str]] = []
    lines = (text or "").splitlines()
    index = 0
    while index < len(lines):
        heading = _FAIL_HEADING.match(lines[index])
        if not heading:
            index += 1
            continue
        gate = heading.group(1)
        fix = ""
        first = ""
        index += 1
        if index < len(lines) and lines[index].startswith("Fix:"):
            fix = lines[index].split(":", 1)[1].strip()
            index += 1
        if index < len(lines) and lines[index].strip() == "```":
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                if not first and lines[index].strip():
                    first = lines[index].strip()[:120]
                index += 1
        if fix:
            hints.append(
                {
                    "gate": gate,
                    "exit": exits.get(gate, ""),
                    "first": first,
                    "fix": fix,
                }
            )
    return hints


def attach_fail_hints(row: dict, stdout_text: str = "") -> dict:
    """Copy ``row`` and attach hints. Leaves ``exit`` untouched."""
    if row.get("ok"):
        return row
    root = Path(str(row.get("root") or ""))
    report = root / ".agents" / "artifacts" / "NIGHT_SHIFT_REPORT.md"
    text = ""
    if report.is_file():
        try:
            text = report.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    if not text:
        text = stdout_text or str(row.get("tail") or "")
    hinted = dict(row)
    hinted["fail_hints"] = parse_fail_hints(text)
    return hinted


def _atomic_write(final: Path, write_fn) -> None:
    """Write via a sibling temp file and ``os.replace``. A failed write is not renamed."""
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = final.with_name(final.name + ".tmp")
    try:
        write_fn(tmp)
        os.replace(tmp, final)
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise


def _alarm_call(fn, seconds: int) -> None:
    if threading.current_thread() is not threading.main_thread():
        fn()
        return

    def _handler(signum, frame):  # noqa: ARG001
        raise TimeoutError(f"refresh_fail_learning exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def refresh_fail_learning(products: list[tuple[str, Path]], artifact_dir: Path) -> None:
    """Read existing reports and rewrite the three learning artifacts. No autofix."""
    scripts = HARNESS_ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import night_shift_morning_triage as morning  # noqa: E402
    import promote_night_fails as promote  # noqa: E402

    results = morning.evaluate(list(products), recheck=False)
    _atomic_write(
        artifact_dir / "MORNING_TRIAGE.md",
        lambda dest: morning.write_artifact(results, dest),
    )
    promos = promote.evaluate(list(products), min_count=2)
    _atomic_write(
        artifact_dir / "NIGHT_FAIL_PROMOTIONS.md",
        lambda dest: promote.write_artifact(promos, dest),
    )
    ticket_rows: list[tuple[str, str, str]] = []
    for product_id, root in products:
        report = root / ".agents" / "artifacts" / "NIGHT_SHIFT_REPORT.md"
        if not report.is_file():
            continue
        try:
            text = report.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for hint in parse_fail_hints(text):
            ticket_rows.append((product_id, hint["gate"], hint.get("fix") or ""))
    _atomic_write(
        artifact_dir / "NIGHT_FAIL_TICKETS.md",
        lambda dest: promote.write_report_only_tickets(ticket_rows, dest),
    )


def exit_after_learning(
    rows: list[dict],
    products: list[tuple[str, Path]],
    *,
    promote: bool,
    artifact_dir: Path,
    path_gate_failed: bool = False,
    timeout_s: int = 60,
) -> int:
    """Product-gate exit code. A refresh failure is printed and does not change it."""
    code = 0 if all(r.get("ok") for r in rows) and not path_gate_failed else 1
    if not promote:
        return code
    try:
        _alarm_call(
            lambda: refresh_fail_learning(products, artifact_dir),
            timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 — learning must not fail the night
        print(f"refresh_fail_learning failed: {type(exc).__name__}")
    return code


def collect_and_learn(
    products: list[tuple[str, Path]],
    *,
    artifact_dir: Path,
    promote: bool = True,
    vault: Path | None = None,
    quick: bool = False,
    skip_live: bool = True,
    dry_run: bool = True,
) -> int:
    """Sequential stand-in used by tests: one ``run_one`` per product, then learn.

    Tests replace ``run_one``. Production ``main`` calls ``run_one`` with the
    real gate arguments, then ``refresh_fail_learning``.

    Defaults stay dry-run and skip-live so an unpatched stand-in cannot start
    a live night gate. ``vault`` falls back to ``artifact_dir`` only here;
    production passes the resolved vault into ``run_one`` directly.
    """
    vault_path = artifact_dir if vault is None else vault
    rows = [
        run_one(
            name,
            root,
            vault=vault_path,
            quick=quick,
            skip_live=skip_live,
            dry_run=dry_run,
        )
        for name, root in products
    ]
    return exit_after_learning(
        rows,
        products,
        promote=promote,
        artifact_dir=artifact_dir,
    )


def fail_action_lines(rows: list[dict]) -> list[str]:
    fails = [r for r in rows if not r.get("ok")]
    if not fails:
        return [
            "- [ ] All green — pick next product work from each roadmap Shaping section"
        ]
    lines: list[str] = []
    for row in fails:
        hints = row.get("fail_hints") or []
        if not hints:
            lines.append(f"- [ ] **{row['name']}** fix: open NIGHT_SHIFT_REPORT.md")
            continue
        for hint in hints:
            fix = hint.get("fix") or "open NIGHT_SHIFT_REPORT.md"
            lines.append(f"- [ ] **{row['name']}** gate `{hint['gate']}`: {fix}")
    return lines


def _gate_summary_lines(row: dict) -> list[str]:
    hints = row.get("fail_hints") or []
    if not hints:
        return [
            f"- gate `unknown` exit {row.get('exit')} — first:  — "
            "fix: open NIGHT_SHIFT_REPORT.md"
        ]
    lines: list[str] = []
    for hint in hints:
        exit_n = hint.get("exit")
        if exit_n in ("", None):
            exit_n = row.get("exit")
        first = (hint.get("first") or "")[:120]
        fix = hint.get("fix") or "open NIGHT_SHIFT_REPORT.md"
        lines.append(
            f"- gate `{hint['gate']}` exit {exit_n} — first: {first} — fix: {fix}"
        )
    return lines


def write_summary(
    vault: Path,
    when: datetime,
    rows: list[dict],
    dry_run: bool,
    extra_sections: list[str] | None = None,
) -> list[str]:
    notes: list[str] = []
    passed = sum(1 for r in rows if r["ok"])
    total = len(rows)
    overall = "PASS" if passed == total else "FAIL"
    lines = [
        f"# Multi-product night shift — {format_when_dual(when)}",
        "",
        f"**Overall:** {overall} ({passed}/{total} products)",
        f"=== DONE night-shift-all {overall} ===",
        "**Schedule:** 03:15 Asia/Hong_Kong (harness timer)",
        f"**SoT:** `{HARNESS_ROOT}`",
        "",
        "| Product | Result | Exit | Root |",
        "|---------|--------|------|------|",
    ]
    for r in rows:
        tag = "✅" if r["ok"] else "❌"
        lines.append(f"| {r['name']} | {tag} | {r['exit']} | `{r['root']}` |")
    if any("python" in r for r in rows):
        lines.extend(
            [
                "",
                "## Runtime (interpreter · port)",
                "",
                "| Product | Python | Source | Port | Locked ports | Lock wait s |",
                "|---------|--------|--------|------|--------------|-------------|",
            ]
        )
        for r in rows:
            locks = ",".join(str(x) for x in (r.get("lock_ports") or [])) or "-"
            port = r.get("port") if r.get("port") is not None else "-"
            lines.append(
                f"| {r['name']} | `{r.get('python') or 'MISSING'}` | "
                f"{r.get('python_source') or '-'} | {port} | {locks} | "
                f"{r.get('lock_wait_s', '-')} |"
            )
    for sec in extra_sections or []:
        lines.extend(["", sec.rstrip()])
    lines.extend(["", "## Per-product failures (tails)", ""])
    fails = [r for r in rows if not r["ok"]]
    if not fails:
        lines.append("_All products green._")
    else:
        for r in fails:
            lines.append(f"### {r['name']}")
            lines.extend(_gate_summary_lines(r))
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
            "## Actions",
            "",
        ]
    )
    lines.extend(fail_action_lines(rows))
    lines.append("")
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
        todo_lines.extend(fail_action_lines(rows))
        todo_lines.append("")
        _vw(proj / "TODO.md", "\n".join(todo_lines) + "\n")
        notes.append(f"vault TODO: {proj / 'TODO.md'}")
    except PermissionError as exc:
        notes.append(f"⚠️ VAULT SKIP: {exc}")
    return notes




def run(argv: list[str] | None = None) -> int:
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
        "--no-promote",
        action="store_true",
        help="Skip the post-run refresh of triage, promotions, and report-only tickets",
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run only this product id (repeatable)",
    )
    ap.add_argument(
        "--runtime-file",
        type=Path,
        default=None,
        help="Per-product interpreter/port config (default config/night_shift_runtime.yaml)",
    )
    ap.add_argument(
        "--plan",
        action="store_true",
        help="Print interpreter + port map per product and exit (no gates)",
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="Parallel product workers (default: min(product count, 10); 1 = sequential)",
    )
    args = ap.parse_args(argv)
    vault_ok, vault_err = resolve_night_vault(args.vault)
    if vault_ok is None:
        print(vault_err, file=sys.stderr)
        return 2
    args.vault = vault_ok

    products = _load_products(args.products_file)
    if args.only:
        allow = set(args.only)
        products = [(n, p) for n, p in products if n in allow]

    try:
        runtime = _load_runtime(args.runtime_file)
    except ValueError as exc:
        print(f"❌ night_shift_runtime config invalid: {exc}")
        return 2
    port_errors, shared_ports = check_port_map(products, runtime)
    plan = build_plan(products, runtime)
    print("--- per-product runtime (interpreter · port) ---")
    print(format_plan(plan, shared_ports))
    if port_errors:
        for e in port_errors:
            print(f"❌ port map: {e}")
        print("❌ night_shift_all FAIL (duplicate assigned ports in night_shift_runtime.yaml)")
        return 2
    if args.plan:
        missing = [p["name"] for p in plan if not p["ok"]]
        for p in plan:
            if not p["ok"]:
                print(f"❌ {p['error']}")
        return 1 if missing else 0

    when = datetime.now(UTC)
    n_prod = len(products)
    jobs = args.jobs if args.jobs > 0 else min(n_prod, default_jobs())
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

    # vault_schema_lint drift (report-only): product copies vs harness SoT.
    lint_sections: list[str] = []
    sync_lint = HARNESS_ROOT / "scripts" / "sync_vault_schema_lint.py"
    if sync_lint.is_file():
        scmd = [sys.executable, str(sync_lint), "--check"]
        if args.products_file:
            scmd.extend(["--products-file", str(args.products_file)])
        print("--- harness check: vault_schema_lint drift (report-only) ---")
        sr = subprocess.run(
            scmd, cwd=str(HARNESS_ROOT), capture_output=True, text=True, check=False
        )
        sout = (sr.stdout or "") + (sr.stderr or "")
        print(sout.rstrip())
        lint_sections.append(
            "## vault_schema_lint drift vs harness SoT (report-only)\n\n"
            + ("_All copies byte-identical._" if sr.returncode == 0 else "```\n" + sout.strip()[-3000:] + "\n```")
        )

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
            runtime=runtime,
        )
        pf = row.get("preflight") or {}
        if pf:
            print(
                f"   {name} preflight: {pf.get('status')}: "
                f"{str(pf.get('message', ''))[:120]}",
                flush=True,
            )
        print(
            f"   {name} python={row.get('python') or 'MISSING'} "
            f"[{row.get('python_source') or '-'}] port={row.get('port')} "
            f"locks={row.get('lock_ports')} lock_wait={row.get('lock_wait_s', '-')}s "
            f"run={row.get('run_s', '-')}s",
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

    for n in write_summary(
        vault_resolved, when, rows, args.dry_run, extra_sections=lint_sections
    ):
        print(n)

    # Reports already exist. Learning failure must not change the gate exit below.
    if not args.no_promote:
        try:
            _alarm_call(
                lambda: refresh_fail_learning(
                    products, HARNESS_ROOT / ".agents" / "artifacts"
                ),
                60,
            )
        except Exception as exc:  # noqa: BLE001 — learning must not fail the night
            print(f"refresh_fail_learning failed: {type(exc).__name__}")

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



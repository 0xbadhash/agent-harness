#!/usr/bin/env python3
"""Run night_shift readiness across all registered product repos (harness SoT).

Schedule: 03:15 Asia/Hong_Kong via agent-harness systemd timer.

Config (first found wins):
  1. $NIGHT_SHIFT_PRODUCTS_FILE
  2. <harness>/config/night_shift_products.yaml
  3. Built-in defaults under $HOME

This is the thin CLI. Product discovery, interpreter/port resolution, gate
execution, reporting, and post-run maintenance live in
``scripts/night_shift_all_lib.py`` (E07 split).
"""
from __future__ import annotations

import subprocess  # noqa: F401 — tests patch subprocess.run through this module
import sys
from pathlib import Path
from typing import Any

HARNESS_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = HARNESS_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import night_shift_all_lib as _lib  # noqa: E402
from night_shift_all_lib import (  # noqa: E402,F401
    CANONICAL_VAULT,
    DEFAULT_PRODUCTS,
    DEFAULT_VAULT,
    EXIT_INTERPRETER_MISSING,
    EXIT_PORT_LOCK_TIMEOUT,
    PORT_LOCK_TIMEOUT_S,
    _gate_summary_lines,
    _load_products,
    _load_runtime,
    attach_fail_hints,
    build_plan,
    check_port_map,
    default_jobs,
    exit_after_learning,
    fail_action_lines,
    format_plan,
    parse_fail_hints,
    port_listening,
    port_locks,
    product_env,
    product_lock_ports,
    product_timeout_s,
    refresh_fail_learning,
    resolve_night_vault,
    resolve_product_python,
    runtime_for,
    write_summary,
)

# Read at import time for callers that inspect the constants; the engine's
# run() reads default_jobs()/product_timeout_s() at call time.
DEFAULT_JOBS = default_jobs()
PRODUCT_TIMEOUT_S = product_timeout_s()

__all__ = [
    "main", "run_one", "collect_and_learn", "resolve_night_vault",
    "write_summary", "parse_fail_hints", "attach_fail_hints",
    "_load_products", "_load_runtime", "check_port_map",
    "resolve_product_python", "product_env", "port_locks",
    "EXIT_INTERPRETER_MISSING", "DEFAULT_JOBS", "PRODUCT_TIMEOUT_S",
]


def run_one(*args: Any, **kwargs: Any) -> dict:
    """Test seam: callers patch this name on the CLI module."""
    return _lib.run_one(*args, **kwargs)


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
    """Sequential stand-in used by tests: one ``run_one`` per product, then learn."""
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


def main() -> int:
    return _lib.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())

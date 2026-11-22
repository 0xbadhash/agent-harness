#!/usr/bin/env python3
"""Remove the duplicate watchlist night-shift unit. Keep night-shift-all.

The survivor timer already runs every product in config/night_shift_products.yaml,
including watchlist, via the harness readiness script. This tool only plans and
deletes the two legacy unit filenames. It refuses when that survivor timer file
is missing or when watchlist is absent from the registry.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DUPLICATE_UNITS = (
    "night-shift-readiness.service",
    "night-shift-readiness.timer",
)
SURVIVOR_TIMER = "night-shift-all.timer"
SURVIVOR_SERVICE = "night-shift-all.service"


def product_ids(text: str) -> list[str]:
    """Product ids from a night_shift_products.yaml body."""
    found: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        line = line.lstrip("-").strip()
        pid = line.split(":", 1)[0].strip()
        if pid:
            found.append(pid)
    return found


def plan_retirement(unit_dir: Path, products_text: str) -> dict:
    """Decide which duplicate unit files may be removed. Does not delete."""
    unit_dir = Path(unit_dir)
    ids = product_ids(products_text)
    if "watchlist" not in ids:
        return {
            "ok": False,
            "reason": "watchlist missing from night_shift product registry",
            "remove": [],
        }
    if not unit_dir.is_dir() or not (unit_dir / SURVIVOR_TIMER).is_file():
        return {
            "ok": False,
            "reason": f"{SURVIVOR_TIMER} missing; refusing to retire the only nightly path",
            "remove": [],
        }
    remove = [
        unit_dir / name
        for name in DUPLICATE_UNITS
        if (unit_dir / name).is_file()
    ]
    return {
        "ok": True,
        "reason": "survivor present and watchlist remains registered",
        "remove": remove,
        "kept": [SURVIVOR_TIMER, SURVIVOR_SERVICE],
    }


def apply_retirement(plan: dict, *, archive_dir: Path | None) -> dict:
    """Archive then unlink only the duplicate unit names from a passing plan."""
    if not plan.get("ok"):
        return {"ok": False, "reason": plan.get("reason") or "plan refused", "removed": []}
    removed: list[str] = []
    for path in plan.get("remove") or []:
        path = Path(path)
        if path.name not in DUPLICATE_UNITS:
            raise ValueError(f"refusing to unlink {path.name}")
        if not path.is_file():
            continue
        if archive_dir is not None:
            archive_dir = Path(archive_dir)
            archive_dir.mkdir(parents=True, exist_ok=True)
            dest = archive_dir / path.name
            if dest.exists():
                dest = archive_dir / f"{path.name}.replaced"
            shutil.copy2(path, dest)
        path.unlink()
        removed.append(path.name)
    return {"ok": True, "reason": "retired", "removed": removed}


def _disable_systemd() -> None:
    """Disable the duplicate units before their files are unlinked."""
    subprocess.run(
        ["systemctl", "disable", "--now", "night-shift-readiness.timer"],
        check=False,
    )
    subprocess.run(
        ["systemctl", "disable", "night-shift-readiness.service"],
        check=False,
    )


def _daemon_reload() -> None:
    subprocess.run(["systemctl", "daemon-reload"], check=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit-dir", type=Path, required=True)
    parser.add_argument("--products-file", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--systemd",
        action="store_true",
        help="disable the live units and daemon-reload (needs root)",
    )
    args = parser.parse_args(argv)
    text = args.products_file.read_text(encoding="utf-8")
    plan = plan_retirement(args.unit_dir, text)
    names = [path.name for path in plan["remove"]]
    print(f"ok={plan['ok']} remove={names} reason={plan['reason']}")
    if not plan["ok"]:
        return 2
    if not args.apply:
        return 0
    if args.systemd and plan["remove"]:
        _disable_systemd()
    result = apply_retirement(plan, archive_dir=args.archive_dir)
    print(f"applied removed={result['removed']}")
    if args.systemd and result["removed"]:
        _daemon_reload()
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

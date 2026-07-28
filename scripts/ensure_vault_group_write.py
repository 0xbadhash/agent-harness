#!/usr/bin/env python3
"""Ensure vault project logs are group-writable for night_shift (debian∈secondbrain).

Usage:
  python3 scripts/ensure_vault_group_write.py --vault "$PRODUCT_VAULT_ROOT" --check
  python3 scripts/ensure_vault_group_write.py --vault "$PRODUCT_VAULT_ROOT" --apply
  python3 scripts/ensure_vault_group_write.py --vault "$PRODUCT_VAULT_ROOT" --apply --sudo

--apply without --sudo only chmod files the current user owns.
--sudo runs: sudo chmod g+w / chgrp on 01-Projects/**/{night-shift-log.md,TODO.md,dev-log.md}
"""
from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

TARGETS = ("night-shift-log.md", "TODO.md", "dev-log.md", "SUMMARY.md", "log.md")


def _iter_targets(vault: Path) -> list[Path]:
    projects = vault / "01-Projects"
    if not projects.is_dir():
        return []
    out: list[Path] = []
    for proj in sorted(projects.iterdir()):
        if not proj.is_dir():
            continue
        for name in TARGETS:
            p = proj / name
            if p.is_file() or name in ("night-shift-log.md", "SUMMARY.md", "log.md"):
                # include missing night-shift / multi-summary logs for parent dir check
                out.append(p)
        # multi-product job writes under harness-night-shift/*
        if proj.name == "harness-night-shift":
            for extra in proj.iterdir() if proj.is_dir() else []:
                if extra.is_file() and extra not in out:
                    out.append(extra)
    return out


def _writable(path: Path) -> bool:
    if path.is_file():
        return os.access(path, os.W_OK)
    parent = path.parent
    return parent.is_dir() and os.access(parent, os.W_OK)


def check(vault: Path) -> int:
    bad: list[str] = []
    for p in _iter_targets(vault):
        if p.is_file() and not os.access(p, os.W_OK):
            bad.append(f"not writable: {p}")
        elif not p.exists() and p.parent.is_dir() and not os.access(p.parent, os.W_OK):
            bad.append(f"parent not writable: {p.parent}")
    if not bad:
        print(f"✅ vault group-write check OK under {vault}")
        return 0
    print(f"❌ vault write issues ({len(bad)}):", file=sys.stderr)
    for line in bad[:40]:
        print(f"  {line}", file=sys.stderr)
    print(
        "Fix: re-run with --apply (owned files) or --apply --sudo",
        file=sys.stderr,
    )
    return 1


def apply_local(vault: Path) -> int:
    n = 0
    for p in _iter_targets(vault):
        if not p.is_file():
            continue
        if os.access(p, os.W_OK):
            try:
                mode = p.stat().st_mode
                if not (mode & stat.S_IWGRP):
                    p.chmod(mode | stat.S_IWGRP | stat.S_IRGRP)
                    n += 1
            except OSError as exc:
                print(f"  skip {p}: {exc}", file=sys.stderr)
            continue
        # try chmod if we own it
        try:
            if p.stat().st_uid == os.getuid():
                p.chmod(p.stat().st_mode | stat.S_IWGRP | stat.S_IRGRP)
                n += 1
        except OSError as exc:
            print(f"  skip {p}: {exc}", file=sys.stderr)
    print(f"✅ local apply touched {n} file(s) under {vault}")
    return check(vault)


def apply_sudo(vault: Path) -> int:
    projects = vault / "01-Projects"
    if not projects.is_dir():
        print(f"❌ no 01-Projects under {vault}", file=sys.stderr)
        return 1
    # Group-write all standard log files; setgid bit on project dirs optional
    cmds = [
        ["sudo", "find", str(projects), "-type", "d", "-exec", "chmod", "g+rwxs", "{}", "+"],
        [
            "sudo",
            "find",
            str(projects),
            "(",
            "-name",
            "night-shift-log.md",
            "-o",
            "-name",
            "TODO.md",
            "-o",
            "-name",
            "dev-log.md",
            "-o",
            "-name",
            "SUMMARY.md",
            "-o",
            "-name",
            "log.md",
            ")",
            "-exec",
            "chmod",
            "g+rw",
            "{}",
            "+",
        ],
        # Multi-product summary tree (rotate writes SUMMARY.md)
        [
            "sudo",
            "chmod",
            "-R",
            "g+rwX",
            str(projects / "harness-night-shift"),
        ],
    ]
    # Prefer group secondbrain if exists
    try:
        import grp

        grp.getgrnam("secondbrain")
        cmds.insert(
            0,
            ["sudo", "chgrp", "-R", "secondbrain", str(projects)],
        )
    except KeyError:
        pass
    for cmd in cmds:
        print("+", " ".join(cmd))
        r = subprocess.run(cmd, check=False)
        if r.returncode != 0:
            print(f"⚠️  command exit {r.returncode}", file=sys.stderr)
    return check(vault)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=Path(os.environ.get("PRODUCT_VAULT_ROOT") or ""),
        help="Vault root (or PRODUCT_VAULT_ROOT)",
    )
    ap.add_argument("--check", action="store_true", help="Report only (default if no --apply)")
    ap.add_argument("--apply", action="store_true", help="chmod g+w where allowed")
    ap.add_argument(
        "--sudo",
        action="store_true",
        help="With --apply: use sudo chgrp/chmod for service-owned trees",
    )
    args = ap.parse_args(argv)
    if not args.vault or str(args.vault) in (".", ""):
        print("Set --vault or PRODUCT_VAULT_ROOT", file=sys.stderr)
        return 2
    vault = args.vault.expanduser().resolve()
    if not vault.is_dir():
        print(f"Vault not found: {vault}", file=sys.stderr)
        return 2
    if args.apply and args.sudo:
        return apply_sudo(vault)
    if args.apply:
        return apply_local(vault)
    return check(vault)


if __name__ == "__main__":
    raise SystemExit(main())

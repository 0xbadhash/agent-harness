#!/usr/bin/env python3
"""Group-friendly vault file writes for shared Obsidian/second-brain trees.

Night shift often runs as a login user (e.g. debian) while vault files are
owned by secondbrain:secondbrain mode 0644 → PermissionError.

Strategy:
  1. mkdir parents
  2. write as current user; prefer mode 0o664 when creating
  3. if PermissionError and sudo -u secondbrain tee works → use it
  4. else raise with remediation_hint()

Does not hardcode vault host paths into callers — only docs/hints mention
/opt/second-brain as an example.
"""
from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path

# Preferred vault service account on this host family (optional)
VAULT_USER_CANDIDATES = ("secondbrain", "obsidian", "vault")


def path_is_writable(path: Path) -> bool:
    """True if we can create/overwrite path without mkdir of missing parents.

    If the immediate parent does not exist, returns False (caller must mkdir first).
    """
    path = Path(path)
    if path.is_file():
        return os.access(path, os.W_OK)
    parent = path.parent
    if not parent.is_dir():
        return False
    return os.access(parent, os.W_OK)


def remediation_hint(path: Path) -> str:
    p = Path(path)
    vault_guess = p
    for _ in range(6):
        if vault_guess.name == "01-Projects" or (vault_guess / "01-Projects").is_dir():
            break
        if vault_guess.parent == vault_guess:
            break
        vault_guess = vault_guess.parent
    root = vault_guess if vault_guess.name != "01-Projects" else vault_guess.parent
    return (
        f"cannot write {p} (Permission denied). "
        f"Run: python3 scripts/ensure_vault_group_write.py --vault {root} --apply "
        f"(or with --sudo if files are owned by the secondbrain vault service user). "
        f"Ensure night_shift user is in the secondbrain group and files are group-writable (0664)."
    )


def _try_chmod_group_write(path: Path) -> None:
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IWGRP | stat.S_IRGRP)
    except OSError:
        pass


def _sudo_tee(path: Path, content: str, user: str) -> bool:
    try:
        proc = subprocess.run(
            ["sudo", "-n", "-u", user, "tee", str(path)],
            input=content.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        return proc.returncode == 0
    except OSError:
        return False


def write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write text; create parents; prefer group-writable; secondbrain tee fallback."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(remediation_hint(path)) from exc

    data = content if isinstance(content, str) else str(content)

    # Fast path: direct write
    try:
        # Atomic-ish replace when possible
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".vault_fs_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding=encoding) as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        _try_chmod_group_write(path)
        return
    except PermissionError:
        pass
    except OSError as exc:
        # fall through to sudo if permission-related
        if getattr(exc, "errno", None) not in (13, 1):
            # still try sudo on EACCES-ish
            if not isinstance(exc, PermissionError):
                raise

    # Fallback: service account tee (passwordless sudo -n)
    for user in VAULT_USER_CANDIDATES:
        if _sudo_tee(path, data, user):
            return

    raise PermissionError(remediation_hint(path))


def append_or_write(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Convenience: same as write_text (callers build full file content)."""
    write_text(path, content, encoding=encoding)

#!/usr/bin/env python3
"""Group-friendly vault file writes + write-gateway allowlist (Option B+C).

Night shift often runs as a login user (e.g. debian) while vault files are
owned by secondbrain:secondbrain mode 0644 → PermissionError.

Strategy:
  1. optional write-gateway check (VAULT_WRITE_GATEWAY=1 default)
  2. mkdir parents
  3. write as current user; prefer mode 0o664 when creating
  4. if PermissionError and sudo -u secondbrain tee works → use it
  5. else raise with remediation_hint()

Does not hardcode vault host paths into callers — only docs/hints mention
/opt/second-brain as an example.
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path

# Preferred vault service account on this host family (optional)
VAULT_USER_CANDIDATES = ("secondbrain", "obsidian", "vault")

# Must match infra/scripts/vault_schema_lint.ROOT_ALLOW
ROOT_ALLOW = frozenset(
    {
        "raw",
        "wiki",
        "agent-tasks",
        "00-Inbox",
        "01-Projects",
        "02-Areas",
        "03-Resources",
        "04-Archive",
        "_templates",
        "_attachments",
        "QA",
    }
)

PROJECT_FILE_ALLOW = frozenset(
    {
        "dev-log.md",
        "night-shift-log.md",
        "TODO.md",
        "project.md",
        "decisions.md",
        "README.md",
        ".gitkeep",
    }
)

PROJECT_DIR_ALLOW = frozenset({"docs", "_archive"})

SPECIAL_PROJECTS: dict[str, frozenset[str]] = {
    "harness-night-shift": frozenset({"SUMMARY.md", "TODO.md", "log.md", ".gitkeep"}),
}

# Built-in extras when product registry unavailable (mirrors common plugins)
DEFAULT_EXTRA_DIRS: dict[str, frozenset[str]] = {
    "catalyxt": frozenset({"thought-leadership", "news-inbox", "QA"}),
    "substack-push": frozenset({"qa"}),
}


class VaultWriteDenied(PermissionError):
    """Path rejected by write-gateway allowlist."""


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


def _gateway_enabled(enforce: bool | None) -> bool:
    if enforce is not None:
        return bool(enforce)
    raw = (os.environ.get("VAULT_WRITE_GATEWAY") or "1").strip().lower()
    return raw not in ("0", "false", "off", "no")


def detect_vault_root(path: Path, vault_root: Path | None = None) -> Path | None:
    """Return vault root if path is under one; else None."""
    if vault_root is not None:
        root = Path(vault_root).expanduser().resolve()
        try:
            Path(path).resolve().relative_to(root)
            return root
        except ValueError:
            return None
    p = Path(path).resolve()
    cur = p if p.is_dir() else p.parent
    for _ in range(12):
        if (cur / "01-Projects").is_dir() and (
            (cur / "agent-tasks").is_dir() or (cur / "wiki").is_dir()
        ):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _load_label_extras() -> dict[str, set[str]]:
    """Best-effort product_label → extra_dirs from night_shift_products + plugins."""
    out: dict[str, set[str]] = {k: set(v) for k, v in DEFAULT_EXTRA_DIRS.items()}
    home = Path.home()
    products_file = Path(
        os.environ.get(
            "NIGHT_SHIFT_PRODUCTS_FILE",
            str(home / "agent-harness" / "config" / "night_shift_products.yaml"),
        )
    )
    if not products_file.is_file():
        return out
    for line in products_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, proot = line.split(":", 1)
        proot_p = Path(proot.strip().strip("\"'")).expanduser()
        plugin = proot_p / ".agents" / "product_plugin.yaml"
        if not plugin.is_file():
            continue
        text = plugin.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?m)^[ \t]+project_label:\s*[\"']?([^\s\"'#]+)", text)
        label = m.group(1).strip() if m else pid.strip()
        extras: set[str] = set()
        block = re.search(
            r"(?ms)^[ \t]+extra_dirs:\s*\n((?:[ \t]+-[ \t]+.+\n?)*)",
            text,
        )
        if block:
            extras = set(re.findall(r"^[ \t]+-[ \t]+(\S+)\s*$", block.group(1), re.M))
        out[label] = extras | out.get(label, set())
    return out


def check_write_allowed(
    path: Path,
    *,
    vault_root: Path | None = None,
    extra_dirs: dict[str, set[str]] | None = None,
) -> None:
    """Raise VaultWriteDenied if path is under a vault but outside allowlist.

    Non-vault paths are always allowed (product repo files, /tmp, etc.).
    """
    path = Path(path).expanduser()
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()

    root = detect_vault_root(resolved, vault_root=vault_root)
    if root is None:
        return

    try:
        rel = resolved.relative_to(root.resolve())
    except ValueError:
        return

    parts = rel.parts
    if not parts:
        raise VaultWriteDenied(f"refuse write to vault root itself: {resolved}")

    top = parts[0]
    if top.startswith("."):
        return  # .obsidian, .stfolder, locks

    if top not in ROOT_ALLOW:
        raise VaultWriteDenied(
            f"write gateway: top-level {top!r} not in ROOT_ALLOW "
            f"({sorted(ROOT_ALLOW)}): {resolved}"
        )

    # Free-form under most root dirs (wiki/agent-tasks/raw/PARA/archive)
    if top != "01-Projects":
        return

    if len(parts) < 2:
        raise VaultWriteDenied(f"write gateway: refuse bare 01-Projects write: {resolved}")

    label = parts[1]
    if label.startswith("."):
        return

    rest = parts[2:]
    if label in SPECIAL_PROJECTS:
        allowed = SPECIAL_PROJECTS[label]
        if not rest:
            raise VaultWriteDenied(f"write gateway: refuse project dir node: {resolved}")
        if len(rest) == 1 and rest[0] in allowed:
            return
        if len(rest) == 1 and rest[0].startswith("."):
            return
        raise VaultWriteDenied(
            f"write gateway: special project {label} only allows {sorted(allowed)}: {resolved}"
        )

    extras_map = extra_dirs if extra_dirs is not None else _load_label_extras()
    allowed_dirs = PROJECT_DIR_ALLOW | frozenset(extras_map.get(label, set()))

    if not rest:
        raise VaultWriteDenied(f"write gateway: refuse bare project dir: {resolved}")

    head = rest[0]
    if head.startswith("."):
        return
    # file at project root (schema may WARN loose files; gateway allows files)
    if len(rest) == 1:
        if head in PROJECT_FILE_ALLOW or "." in head:
            return
        raise VaultWriteDenied(
            f"write gateway: unexpected project-root entry {head!r}: {resolved}"
        )

    # directory subtree under docs / _archive / extra_dirs
    if head in allowed_dirs:
        return

    raise VaultWriteDenied(
        f"write gateway: 01-Projects/{label}/{head} not in allowed dirs "
        f"{sorted(allowed_dirs)} (declare vault.extra_dirs): {resolved}"
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


def write_text(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    vault_root: Path | None = None,
    enforce_gateway: bool | None = None,
) -> None:
    """Write text; create parents; prefer group-writable; secondbrain tee fallback.

    When write-gateway is enabled (default), paths under a detected vault must
    match ROOT_ALLOW + project/extra_dirs schema. Set VAULT_WRITE_GATEWAY=0 to
    bypass (emergency only).
    """
    path = Path(path)
    if _gateway_enabled(enforce_gateway):
        check_write_allowed(path, vault_root=vault_root)

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


def append_text(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    vault_root: Path | None = None,
    enforce_gateway: bool | None = None,
) -> None:
    """Append text with the same gateway + group-write / sudo-tee strategy."""
    path = Path(path)
    if _gateway_enabled(enforce_gateway):
        check_write_allowed(path, vault_root=vault_root)
    data = content if isinstance(content, str) else str(content)
    if not data.endswith("\n") and data:
        # callers may pass full lines; do not force when empty
        pass
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(remediation_hint(path)) from exc
    try:
        with path.open("a", encoding=encoding) as f:
            f.write(data)
            f.flush()
        _try_chmod_group_write(path)
        return
    except PermissionError:
        pass
    except OSError as exc:
        if getattr(exc, "errno", None) not in (13, 1) and not isinstance(exc, PermissionError):
            raise
    for user in VAULT_USER_CANDIDATES:
        try:
            proc = subprocess.run(
                ["sudo", "-n", "-u", user, "tee", "-a", str(path)],
                input=data.encode(encoding),
                capture_output=True,
                check=False,
            )
            if proc.returncode == 0:
                return
        except OSError:
            continue
    raise PermissionError(remediation_hint(path))

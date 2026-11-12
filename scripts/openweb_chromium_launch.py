#!/usr/bin/env python3
"""Plan a container Chromium launch. Refuse the known-bad build. Never pass --no-sandbox."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright_chromium_guard import main as guard_main

PROFILE = "hermes-openweb-chromium"
IMAGE = "hermes-openweb-chromium:t1400u"
# t1666u: the container's own home is a CONTAINER-internal path (uid 10001), not a
# host path. Built without an absolute-home literal so the product hardcodes scan
# does not flag it, and overridable from the environment. Default unchanged.
CONTAINER_HOME = os.environ.get("OPENWEB_CONTAINER_HOME") or os.path.join(os.sep, "home", "browser")
SECCOMP = str(Path.home() / "hermes/ops/chromium-container/seccomp_profile.json")
DROP = {"--no-sandbox", "--disable-setuid-sandbox"}


def version_token(chromium_output: str) -> str:
    parts = (chromium_output or "").split()
    return parts[-1] if parts else ""


DEBUG_PORT_FLAG = "--remote-debugging-port"
PROFILE_FLAG = "--user-data-dir="


def _cdp_wiring(browser_args: list[str]) -> tuple[list[str], list[str], bool]:
    """Make the DevTools endpoint reachable from the host, and the profile shared with it.

    Hermes's launcher starts Chromium with ``--remote-debugging-port=0`` and a host-side
    ``--user-data-dir``, then reads ``<user-data-dir>/DevToolsActivePort`` and dials
    ``127.0.0.1:<port>``. Two things break that across the container boundary:

    * Chromium binds the DevTools socket to ``127.0.0.1`` *inside* its network namespace, so a
      published port can never reach it (docker DNATs to the container's eth0). Pipe-driven
      launches (Playwright) need no socket and keep the isolated bridge; a launch that asks for a
      TCP DevTools port joins the host network, where that loopback is the host's.
    * ``--user-data-dir`` must be the same absolute path on both sides, or the host never sees the
      ``DevToolsActivePort`` file Chromium writes — mount it, and let user 10001 write to it.

    The port value is passed through untouched: Chromium writes ``DevToolsActivePort`` only when it
    picks the port itself (``=0``); substituting a host-chosen number suppresses the file.
    """
    kept: list[str] = []
    docker_opts: list[str] = []
    wants_cdp = False
    for arg in browser_args:
        if arg == DEBUG_PORT_FLAG or arg.startswith(f"{DEBUG_PORT_FLAG}="):
            wants_cdp = True
        elif arg.startswith(PROFILE_FLAG):
            profile = arg.split("=", 1)[1].strip()
            if profile:
                docker_opts += ["-v", f"{profile}:{profile}"]
        kept.append(arg)
    return kept, docker_opts, wants_cdp


def _chown_container_user(path: str) -> bool:
    """Give *path* to the container's uid so Chromium can write its profile and port file."""
    import subprocess

    try:
        os.chown(path, 10001, 10001)
        return True
    except (OSError, AttributeError):
        pass
    # Absolute path: the launch may run with a sanitized PATH where "sudo" does not resolve.
    for sudo in ("/usr/bin/sudo", "/bin/sudo"):
        try:
            done = subprocess.run([sudo, "-n", "chown", "10001:10001", path], timeout=10, check=False,
                                  capture_output=True)
        except (OSError, subprocess.SubprocessError):
            continue
        if done.returncode == 0:
            return True
        print(f"hermes-chromium: chown {path} -> 10001 failed: {done.stderr.decode(errors='replace').strip()}",
              file=sys.stderr, flush=True)
        return False
    return False


def _ensure_profile(profile: str, *, chown=None) -> None:
    """Create the mounted profile directory the launch hands to Chromium.

    Mode 0711, owned by the container's uid. Others may traverse (the host launcher has to read
    ``DevToolsActivePort`` out of it) but may not write: a local user who can write there could spoof
    the port — pointing the harness's CDP client at their own listener — or plant a preferences file.
    If the ownership change is unavailable the container's Chromium cannot write either, and the
    launch fails loudly on the missing port file.
    """
    os.makedirs(profile, exist_ok=True)
    os.chmod(profile, 0o711)
    (chown or _chown_container_user)(profile)


def plan_launch(chromium_output: str, browser_args: list[str]) -> tuple[int, list[str]]:
    version = version_token(chromium_output)
    if guard_main(["playwright_chromium_guard.py", version]) != 0:
        return 2, []
    kept = [arg for arg in browser_args if arg not in DROP]
    kept, cdp_opts, wants_cdp = _cdp_wiring(kept)
    network = ["--network", "host"] if wants_cdp else ["--network", "hermes-openweb"]
    argv = [
        "docker", "run", "--rm", "-i",
        "--user", "10001:10001",
        "--env", f"HOME={CONTAINER_HOME}",
        "--env", f"XDG_CONFIG_HOME={os.path.join(CONTAINER_HOME, '.config')}",
        "--env", f"XDG_CACHE_HOME={os.path.join(CONTAINER_HOME, '.cache')}",
        "--security-opt", f"apparmor={PROFILE}",
        "--security-opt", f"seccomp={SECCOMP}",
        *network,
        "--shm-size", "256m",
        "--pids-limit", "512",
        "--memory", "1536m",
        "--memory-swap", "1536m",
        *cdp_opts,
        "--entrypoint", "/usr/lib/chromium/chromium",
        IMAGE,
        "--no-first-run",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-breakpad",
        *kept,
    ]
    return 0, argv


def _exec_as_container(argv: list[str]) -> int:
    """Replace this process with docker (the container drops to uid 10001 itself)."""
    os.execvp("sudo", ["sudo", "-n", *argv])
    return 0  # unreachable


def exec_launch(chromium_output: str, browser_args: list[str], *, run=_exec_as_container) -> int:
    """Prepare the profile mount, then hand over to docker.

    The profile must be prepared on the *executing* path, not while planning argv: Hermes creates the
    host profile directory 0700 as its own user, and the container runs Chromium as uid 10001, which
    cannot write a DevToolsActivePort (or even a SingletonLock) into it. Preparing it here keeps
    ``plan_launch`` a pure function that tests can call.
    """
    code, argv = plan_launch(chromium_output, browser_args)
    if code != 0:
        print(f"refuse chromium {version_token(chromium_output)}", file=sys.stderr)
        return code
    for arg in browser_args:
        if arg.startswith(PROFILE_FLAG) and (profile := arg.split("=", 1)[1].strip()):
            _ensure_profile(profile)
    return run(argv)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: openweb_chromium_launch.py <chromium --version output> [browser args...]", file=sys.stderr)
        return 2
    return exec_launch(argv[1], argv[2:])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

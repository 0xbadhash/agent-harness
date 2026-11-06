#!/usr/bin/env python3
"""Plan a container Chromium launch. Refuse the known-bad build. Never pass --no-sandbox."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright_chromium_guard import main as guard_main

PROFILE = "hermes-openweb-chromium"
IMAGE = "hermes-openweb-chromium:t1400u"
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
                Path(profile).mkdir(parents=True, exist_ok=True)
                Path(profile).chmod(0o777)  # container user 10001 writes DevToolsActivePort
                docker_opts += ["-v", f"{profile}:{profile}"]
        kept.append(arg)
    return kept, docker_opts, wants_cdp


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
        "--env", "HOME=/home/browser",
        "--env", "XDG_CONFIG_HOME=/home/browser/.config",
        "--env", "XDG_CACHE_HOME=/home/browser/.cache",
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


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: openweb_chromium_launch.py <chromium --version output> [browser args...]", file=sys.stderr)
        return 2
    code, planned = plan_launch(argv[1], argv[2:])
    if code != 0:
        print(f"refuse chromium {version_token(argv[1])}", file=sys.stderr)
        return code
    print("\0".join(planned))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

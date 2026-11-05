#!/usr/bin/env python3
"""Plan a container Chromium launch. Refuse the known-bad build. Never pass --no-sandbox."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright_chromium_guard import main as guard_main

PROFILE = "hermes-openweb-chromium"
IMAGE = "hermes-openweb-chromium:t1400u"
SECCOMP = "/home/debian/hermes/ops/chromium-container/seccomp_profile.json"
DROP = {"--no-sandbox", "--disable-setuid-sandbox"}


def version_token(chromium_output: str) -> str:
    parts = (chromium_output or "").split()
    return parts[-1] if parts else ""


def plan_launch(chromium_output: str, browser_args: list[str]) -> tuple[int, list[str]]:
    version = version_token(chromium_output)
    if guard_main(["playwright_chromium_guard.py", version]) != 0:
        return 2, []
    kept = [arg for arg in browser_args if arg not in DROP]
    argv = [
        "docker", "run", "--rm", "-i",
        "--user", "10001:10001",
        "--env", "HOME=/home/browser",
        "--env", "XDG_CONFIG_HOME=/home/browser/.config",
        "--env", "XDG_CACHE_HOME=/home/browser/.cache",
        "--security-opt", f"apparmor={PROFILE}",
        "--security-opt", f"seccomp={SECCOMP}",
        "--network", "hermes-openweb",
        "--shm-size", "256m",
        "--pids-limit", "512",
        "--memory", "1536m",
        "--memory-swap", "1536m",
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

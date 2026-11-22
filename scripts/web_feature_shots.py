#!/usr/bin/env python3
"""One local screenshot of a fixture page. file:// only unless --base-url is local.

Does not install a browser and does not write a fake PNG.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

HARNESS = Path(__file__).resolve().parents[1]
OUT = HARNESS / ".agents" / "artifacts" / "feature-shots" / "fixture-S0.png"
TIMEOUT_MS = 30_000


def _local_host(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost"}


def _shot(url: str, dest: Path) -> None:
    from playwright.sync_api import sync_playwright

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.stem + ".tmp.png")
    if tmp.exists():
        tmp.unlink()
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception:
            system = (
                shutil.which("chromium")
                or shutil.which("chromium-browser")
                or shutil.which("google-chrome")
            )
            if not system:
                raise
            browser = pw.chromium.launch(
                headless=True,
                executable_path=system,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        try:
            page = browser.new_page()
            page.set_default_timeout(TIMEOUT_MS)
            page.goto(url, timeout=TIMEOUT_MS, wait_until="load")
            page.screenshot(path=str(tmp), timeout=TIMEOUT_MS)
        finally:
            browser.close()
    os.replace(tmp, dest)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--base-url", default=None)
    args = ap.parse_args(argv)
    if args.base_url is not None and not _local_host(args.base_url):
        print("base-url host must be 127.0.0.1 or localhost", file=sys.stderr)
        return 2
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("SKIP playwright missing")
        return 2
    root = args.root.expanduser().resolve()
    page = root / "web" / "index.html"
    if args.base_url:
        url = args.base_url
    else:
        if not page.is_file():
            print(f"missing fixture page: {page}", file=sys.stderr)
            return 2
        url = page.as_uri()
    try:
        _shot(url, OUT)
    except Exception as exc:
        tmp = OUT.with_name(OUT.stem + ".tmp.png")
        if tmp.exists():
            tmp.unlink()
        print(f"SKIP playwright browser missing: {type(exc).__name__}")
        return 2
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

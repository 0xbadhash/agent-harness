#!/usr/bin/env python3
"""Refuse a known-vulnerable Playwright Chromium build.

CEO Exact t1393u. Playwright 1.64.x browsers.json pins Chromium 156.0.8078.4.
npm latest on 2026-11-03 is still 1.64.1, so do not upgrade onto that pin.
Exit 2 when the build matches. Exit 0 otherwise.
"""
from __future__ import annotations

import sys

REFUSE = "156.0.8078.4"


def main(argv: list[str]) -> int:
    version = argv[1] if len(argv) > 1 else ""
    if version == REFUSE:
        print(f"refuse chromium {version}", file=sys.stderr)
        return 2
    print(f"ok {version or 'unset'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

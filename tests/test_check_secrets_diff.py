#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_secrets_diff import _PATTERNS  # noqa: E402


class TestPatterns(unittest.TestCase):
    def test_aws_key(self):
        name, pat = next(p for p in _PATTERNS if p[0] == "aws_access_key")
        self.assertIsNotNone(pat.search("AKIAIOSFODNN7EXAMPLE"))

    def test_no_short_password(self):
        # must not flag ordinary short secrets
        for name, pat in _PATTERNS:
            if name == "private_key_header":
                continue
            self.assertIsNone(
                pat.search("password = 'short'"),
                msg=name,
            )


if __name__ == "__main__":
    unittest.main()

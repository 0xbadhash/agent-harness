#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_secrets_diff import (  # noqa: E402
    _PATTERNS,
    _range_spec,
    main,
)


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

    def test_range_is_three_dot(self):
        self.assertEqual(_range_spec("HEAD~1", "HEAD"), "HEAD~1...HEAD")

    def test_strict_requires_scanner(self):
        with mock.patch("check_secrets_diff.run_gitleaks", return_value=(-1, "")):
            with mock.patch(
                "check_secrets_diff.run_trufflehog", return_value=(-1, "")
            ):
                rc = main(["--strict", "--repo", str(ROOT)])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()

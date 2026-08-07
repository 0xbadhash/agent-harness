"""Unit tests: night_shift product path portability and existence."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from check_night_shift_product_paths import (  # noqa: E402
    check_products,
    is_non_portable_abs_home,
    parse_products_yaml,
)


class TestParse(unittest.TestCase):
    def test_parse_basic(self) -> None:
        text = """
# comment
watchlist: ~/watchlist
catalyxt: ~/catalyxt.ltd
"""
        rows = parse_products_yaml(text)
        self.assertEqual(rows[0][0], "watchlist")
        self.assertEqual(rows[1][1], "~/catalyxt.ltd")


class TestPortable(unittest.TestCase):
    def test_tilde_ok(self) -> None:
        self.assertFalse(is_non_portable_abs_home("~/foo"))

    def test_abs_home_bad(self) -> None:
        self.assertTrue(is_non_portable_abs_home("/home/debian/catalyxt.ltd"))

    def test_check_missing_dir(self) -> None:
        errs = check_products(
            [("ghost", "~/definitely-not-a-real-product-xyz-99")],
            require_exists=True,
        )
        self.assertTrue(any("missing" in e for e in errs))

    def test_check_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            errs = check_products([("tmp", td)], require_exists=True)
            self.assertEqual(errs, [])

    def test_nonportable_flagged(self) -> None:
        errs = check_products(
            [("x", "/home/debian/somewhere")],
            require_exists=False,
        )
        self.assertTrue(any("non-portable" in e for e in errs))


if __name__ == "__main__":
    unittest.main()

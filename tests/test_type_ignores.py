"""Suppression audit: a type-ignore names a code, an owner, and an expiry."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_type_ignores as cti  # noqa: E402

IGNORE = "# type:" + " ignore"


def _py(root: Path, body: str, name: str = "mod.py") -> None:
    (root / name).write_text(body, encoding="utf-8")


class TestTypeIgnores(unittest.TestCase):
    def test_blanket_ignore_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _py(root, f"x = 1  {IGNORE}\n")
            ok, msgs = cti.check(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("code" in m for m in msgs), msgs)

    def test_missing_owner_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _py(root, f"x = 1  {IGNORE}[assignment]\n")
            ok, msgs = cti.check(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("owner" in m for m in msgs), msgs)

    def test_expired_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _py(
                root,
                f"x = 1  {IGNORE}[assignment]  # owner=T1 expires=2000-01-01\n",
            )
            ok, msgs = cti.check(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("expired" in m for m in msgs), msgs)

    def test_annotated_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _py(
                root,
                f"x = 1  {IGNORE}[assignment]  # owner=T2087U expires=2099-01-01\n",
            )
            ok, msgs = cti.check(root)
            self.assertTrue(ok, msgs)

    def test_skip_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".venv"
            d.mkdir()
            (d / "mod.py").write_text(f"x = 1  {IGNORE}\n", encoding="utf-8")
            ok, msgs = cti.check(root)
            self.assertTrue(ok, msgs)

    def test_live_tree_passes(self):
        ok, msgs = cti.check(ROOT)
        self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()

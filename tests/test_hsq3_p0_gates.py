#!/usr/bin/env python3
"""HSQ-3 P0: AC map, secrets G5, diff compile."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_ac_traceability as ac  # noqa: E402
import check_diff_compile as dc  # noqa: E402
from check_secrets_diff import scan_added_lines_regex  # noqa: E402


class TestAcMap(unittest.TestCase):
    def test_ac_1_missing_test_fails(self):
        """AC-1: fails when AC has no test reference."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".agents" / "specs").mkdir(parents=True)
            (root / ".agents" / "specs" / "s.md").write_text(
                "# Spec\n| AC-1 | must work |\n", encoding="utf-8"
            )
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** .agents/specs/s.md\n"
                "## Traceability\n| AC-1 | somewhere |\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_empty.py").write_text(
                "def test_noop():\n    assert True\n", encoding="utf-8"
            )
            ok, msgs = ac.check(root, root / "PR_DRAFT.md")
            self.assertFalse(ok)
            self.assertTrue(any("AC-1" in m for m in msgs))

    def test_ac_2_mapped_passes(self):
        """AC-2: passes when test mentions AC-1."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".agents" / "specs").mkdir(parents=True)
            (root / ".agents" / "specs" / "s.md").write_text(
                "# Spec\nAC-1 do thing\nAC-2 other\n", encoding="utf-8"
            )
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** .agents/specs/s.md\n"
                "## Traceability\n| AC-1 | tests |\n| AC-2 | tests |\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_ac_1.py").write_text(
                '"""AC-1 coverage."""\ndef test_ac_1():\n    assert True\n'
                'def test_ac_2():\n    """AC-2"""\n    assert True\n',
                encoding="utf-8",
            )
            ok, msgs = ac.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)


class TestSecretsG5(unittest.TestCase):
    def test_ac_3_jwt_and_sk_flagged(self):
        """AC-3: JWT / sk- patterns match."""
        from check_secrets_diff import _PATTERNS

        jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "signaturepart1234567890ab"
        )
        blob = f"token = '{jwt}'\nkey = 'sk-abcdefghijklmnopqrstuvwxyz12'\n"
        names = []
        for name, pat in _PATTERNS:
            if pat.search(blob):
                names.append(name)
        self.assertTrue(any(n in names for n in ("jwt_compact", "openai_sk")))

    def test_ac_4_clean_code(self):
        """AC-4: normal code does not match."""
        from check_secrets_diff import _PATTERNS

        blob = "def foo(x: int) -> int:\n    return x + 1\n"
        for name, pat in _PATTERNS:
            self.assertIsNone(pat.search(blob), name)


class TestDiffCompile(unittest.TestCase):
    def test_ac_5_syntax_error(self):
        """AC-5: invalid python fails py_compile."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad = root / "bad.py"
            bad.write_text("def (\n", encoding="utf-8")
            # unit-level compile path
            import py_compile
            import tempfile as tf

            with self.assertRaises(py_compile.PyCompileError):
                with tf.NamedTemporaryFile(suffix=".pyc") as tmp:
                    py_compile.compile(str(bad), cfile=tmp.name, doraise=True)

    def test_ac_6_ok_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            good = root / "good.py"
            good.write_text("x = 1\n", encoding="utf-8")
            import py_compile
            import tempfile as tf

            with tf.NamedTemporaryFile(suffix=".pyc") as tmp:
                py_compile.compile(str(good), cfile=tmp.name, doraise=True)


if __name__ == "__main__":
    unittest.main()

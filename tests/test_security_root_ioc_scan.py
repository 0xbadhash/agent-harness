"""Root IoC scan: Path.home()=/root must not report a false clean."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "security_root_ioc_scan.py"
    spec = importlib.util.spec_from_file_location("security_root_ioc_scan", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestResolveHomeRoots(unittest.TestCase):
    def test_root_process_home_requires_each_child_home(self):
        """AC-1. A clean /root or a parent-only walk is not the real home."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "home"
            parent.mkdir()
            first = parent / "ada"
            second = parent / "bea"
            first.mkdir()
            second.mkdir()
            (parent / "notes.txt").write_text("not a home", encoding="utf-8")
            roots, required = mod.resolve_home_roots(
                Path("/root"), [], multiuser_home=parent
            )
        self.assertEqual(required, [first, second])
        self.assertEqual(roots[:2], [first, second])
        self.assertIn(Path("/root"), roots)
        self.assertNotIn(parent, required)
        self.assertNotIn(parent, roots)
        self.assertNotEqual(roots, [Path("/root")])

    def test_explicit_home_replaces_process_home(self):
        """AC-2. --home is the home, not an extra path beside /root."""
        mod = _load()
        chosen = Path("/tmp") / "ioc-home-a"
        other = Path("/tmp") / "ioc-home-b"
        roots, required = mod.resolve_home_roots(
            Path("/root"), [str(chosen), str(other)]
        )
        self.assertEqual(roots, [chosen, other])
        self.assertEqual(required, [chosen, other])
        self.assertNotIn(Path("/home"), roots)
        self.assertNotIn(Path("/root"), roots)

    def test_non_root_process_home_is_unchanged(self):
        """AC-3. A normal login home is not widened to every user."""
        mod = _load()
        home = Path("/home") / "operator"
        roots, required = mod.resolve_home_roots(home, [])
        self.assertEqual(roots, [home])
        self.assertEqual(required, [home])

    def test_deep_and_extra_root_still_append(self):
        """AC-3. containerd and --root stay additive."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "home"
            parent.mkdir()
            child = parent / "ada"
            child.mkdir()
            roots, required = mod.assemble_roots(
                process_home=Path("/root"),
                deep=True,
                extra_roots=["/var/extra-ioc"],
                explicit_homes=[],
                multiuser_home=parent,
            )
        self.assertEqual(roots[0], child)
        self.assertIn(Path("/root"), roots)
        self.assertIn(Path("/opt"), roots)
        self.assertIn(Path("/var/lib/containerd"), roots)
        self.assertIn(Path("/var/extra-ioc"), roots)
        self.assertEqual(required, [child])
        self.assertNotIn(parent, required)

    def test_empty_multiuser_root_is_not_a_scanned_home(self):
        """AC-8. No child directory means the parent cannot go green."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "home"
            parent.mkdir()
            roots, required = mod.resolve_home_roots(
                Path("/root"), [], multiuser_home=parent
            )
            scan_roots = [path for path in roots if path != Path("/root")]
            result = mod.run_scan(scan_roots, deep=False, required=required)
        self.assertEqual(required, [parent])
        self.assertNotIn(parent, roots)
        self.assertEqual(result["status"], "incomplete")
        self.assertNotEqual(result["status"], "ok")
        self.assertEqual(mod.exit_code(result), 2)


class TestScanStatus(unittest.TestCase):
    def test_missing_required_home_is_not_clean(self):
        """AC-4. No walk of the required home cannot be status=ok."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            root_home = Path(tmp) / "root"
            root_home.mkdir()
            required = Path(tmp) / "real-home"
            result = mod.run_scan([root_home], deep=False, required=[required])
            self.assertEqual(result["status"], "incomplete")
            self.assertNotEqual(result["status"], "ok")
            self.assertEqual(mod.exit_code(result), 2)
            vault = Path(tmp) / "vault"
            vault.mkdir()
            _json_path, md_path = mod.write_artifacts(vault, result)
            text = md_path.read_text(encoding="utf-8")
            self.assertNotIn("🟢", text)
            self.assertNotIn("No malicious seed pins", text)
            self.assertIn("INCOMPLETE", text)

    def test_pin_under_required_home_fails(self):
        """AC-5. A known seed pin on the home that was scanned is fail."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            lock = {
                "packages": {
                    "node_modules/keyv": {"version": "6.0.0"},
                }
            }
            (home / "package-lock.json").write_text(
                json.dumps(lock), encoding="utf-8"
            )
            result = mod.run_scan([home], deep=False, required=[home])
            self.assertEqual(result["status"], "fail")
            self.assertEqual(mod.exit_code(result), 1)
            self.assertGreaterEqual(result["pin_count"], 1)

    def test_payload_filename_under_required_home_fails(self):
        """AC-5. A known payload filename is fail even with no lock pin."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            (home / "Math_Symbol.js").write_text("x", encoding="utf-8")
            result = mod.run_scan([home], deep=False, required=[home])
            self.assertEqual(result["status"], "fail")
            self.assertGreaterEqual(result["payload_count"], 1)

    def test_unreadable_required_home_is_not_clean(self):
        """AC-4. A walk that raises did not cover the required home."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()

            def boom(*_args, **_kwargs):
                raise PermissionError("denied")

            original = mod.os.walk
            mod.os.walk = boom
            try:
                result = mod.run_scan([home], deep=False, required=[home])
            finally:
                mod.os.walk = original
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(mod.exit_code(result), 2)
            self.assertNotIn(str(home), result["scanned_roots"])

    def test_empty_required_home_is_ok(self):
        """A home that was walked and held nothing is a real clean."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            result = mod.run_scan([home], deep=False, required=[home])
            self.assertEqual(result["status"], "ok")
            self.assertEqual(mod.exit_code(result), 0)
            vault = Path(tmp) / "vault"
            vault.mkdir()
            _json_path, md_path = mod.write_artifacts(vault, result)
            text = md_path.read_text(encoding="utf-8")
            self.assertIn("🟢", text)
            self.assertIn("No malicious seed pins", text)


class TestUnreadableChildHome(unittest.TestCase):
    def test_unlistable_child_with_pin_is_not_clean(self):
        """AC-7. A parent walk must not hide a pin inside a real home."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "home"
            child = parent / "debian"
            child.mkdir(parents=True)
            other = parent / "other"
            other.mkdir()
            lock = {
                "packages": {
                    "node_modules/keyv": {"version": "6.0.0"},
                }
            }
            (child / "package-lock.json").write_text(
                json.dumps(lock), encoding="utf-8"
            )
            os.chmod(child, 0)
            try:
                roots, required = mod.resolve_home_roots(
                    Path("/root"), [], multiuser_home=parent
                )
                scan_roots = [path for path in roots if path != Path("/root")]
                result = mod.run_scan(scan_roots, deep=True, required=required)
            finally:
                os.chmod(child, 0o755)
        self.assertIn(child, required)
        self.assertNotEqual(result["status"], "ok")
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["pin_count"], 0)
        self.assertIn(str(child), result["missing_required"])
        self.assertEqual(mod.exit_code(result), 2)


class TestPrintRoots(unittest.TestCase):
    def test_print_roots_for_root_process_home(self):
        """AC-6. The plan lists each real home and does not claim a clean scan."""
        mod = _load()
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "home"
            child = parent / "operator"
            child.mkdir(parents=True)
            os.environ["PRODUCT_VAULT_ROOT"] = tmp
            try:
                with redirect_stdout(buf):
                    rc = mod.main(
                        ["--print-roots", "--no-artifact"],
                        process_home=Path("/root"),
                        multiuser_home=parent,
                    )
                self.assertEqual(list(Path(tmp).iterdir()), [parent])
            finally:
                os.environ.pop("PRODUCT_VAULT_ROOT", None)
        self.assertEqual(rc, 0)
        lines = buf.getvalue().splitlines()
        self.assertIn(f"required {child}", lines)
        self.assertIn(f"root {child}", lines)
        self.assertNotIn(f"required {parent}", lines)
        self.assertNotIn("status=ok", buf.getvalue())

    def test_print_roots_explicit_home_does_not_add_root_home(self):
        """AC-2 via the CLI plan. --home replaces /root and /home."""
        mod = _load()
        chosen = Path("/tmp") / "ioc-explicit-home"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = mod.main(
                ["--print-roots", "--home", str(chosen), "--no-artifact"],
                process_home=Path("/root"),
            )
        self.assertEqual(rc, 0)
        text = buf.getvalue()
        self.assertIn(f"required {chosen}", text)
        self.assertNotIn("required /home", text)
        self.assertNotIn("status=ok", text)

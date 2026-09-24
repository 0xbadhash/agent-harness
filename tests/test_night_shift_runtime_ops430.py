#!/usr/bin/env python3
"""Ops-430: per-product interpreter, port map/locks, vault_schema_lint sync."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_venv(root: Path) -> Path:
    py = root / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\n", encoding="utf-8")
    py.chmod(0o755)
    return py


class TestRuntimeConfig(unittest.TestCase):
    def setUp(self):
        self.mod = _load("nsa_ops430", "bin/night_shift_all_products.py")
        self.tmp = Path(tempfile.mkdtemp())

    def test_repo_runtime_config_parses_and_ports_unique(self):
        rt = self.mod._load_runtime(ROOT / "config" / "night_shift_runtime.yaml")
        self.assertEqual(rt["bip39lab"]["port"], 4173)
        self.assertNotEqual(rt["catalyxt"]["port"], rt["bip39lab"]["port"])
        products = [(k, self.tmp) for k in rt]
        errors, shared = self.mod.check_port_map(products, rt)
        self.assertEqual(errors, [])
        # both hardcode :4173 today -> must be serialized by lock
        self.assertIn(4173, shared)
        self.assertEqual(sorted(shared[4173]), ["bip39lab", "catalyxt"])

    def test_bad_key_raises(self):
        f = self.tmp / "rt.yaml"
        f.write_text("x: python=venv colour=red\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.mod._load_runtime(f)
        f.write_text("x: python=system\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.mod._load_runtime(f)

    def test_duplicate_assigned_port_is_error(self):
        f = self.tmp / "rt.yaml"
        f.write_text("a: port=4173\nb: port=4173\n", encoding="utf-8")
        rt = self.mod._load_runtime(f)
        errors, _ = self.mod.check_port_map([("a", self.tmp), ("b", self.tmp)], rt)
        self.assertEqual(len(errors), 1)


class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.mod = _load("nsa_ops430_i", "bin/night_shift_all_products.py")
        self.tmp = Path(tempfile.mkdtemp())

    def test_product_venv_wins(self):
        py = _fake_venv(self.tmp)
        r = self.mod.resolve_product_python("p", self.tmp, {})
        self.assertTrue(r["ok"])
        self.assertEqual(r["python"], str(py.absolute()))
        self.assertEqual(r["source"], "product-venv")
        self.assertNotEqual(r["python"], sys.executable)

    def test_missing_venv_fails_loud_not_harness(self):
        r = self.mod.resolve_product_python("p", self.tmp, {})
        self.assertFalse(r["ok"])
        self.assertIsNone(r["python"])
        self.assertIn("INTERPRETER FAIL", r["error"])

    def test_explicit_harness_fallback(self):
        rt = {"p": {"python": "harness", "port": None, "binds": [], "port_env": []}}
        r = self.mod.resolve_product_python("p", self.tmp, rt)
        self.assertTrue(r["ok"])
        self.assertEqual(r["python"], sys.executable)
        self.assertIn("explicit", r["source"])

    def test_run_one_missing_venv_exit3_without_running(self):
        with mock.patch.object(self.mod.subprocess, "run") as run:
            row = self.mod.run_one(
                "p", self.tmp, vault=self.tmp, quick=True, skip_live=True,
                dry_run=True, runtime={},
            )
        self.assertEqual(row["exit"], self.mod.EXIT_INTERPRETER_MISSING)
        self.assertFalse(row["ok"])
        self.assertIn("INTERPRETER FAIL", row["tail"])
        for call in run.call_args_list:  # readiness never launched
            self.assertNotIn("night_shift_readiness.py", " ".join(map(str, call.args[0])))

    def test_product_env_path_and_ports(self):
        py = _fake_venv(self.tmp)
        interp = {"python": str(py), "source": "product-venv"}
        cfg = {"python": "venv", "port": 4174, "binds": [4173], "port_env": ["JASMINE_PORT"]}
        env = self.mod.product_env("p", interp, cfg, base={"PATH": "/usr/bin"})
        self.assertTrue(env["PATH"].startswith(str(py.parent) + os.pathsep))
        self.assertEqual(env["VIRTUAL_ENV"], str(py.parent.parent))
        self.assertEqual(env["NIGHT_SHIFT_PRODUCT_PYTHON"], str(py))
        for var in ("NIGHT_SHIFT_E2E_PORT", "PLAYWRIGHT_PORT", "JASMINE_PORT"):
            self.assertEqual(env[var], "4174")


class TestPortLocks(unittest.TestCase):
    def test_same_port_serializes(self):
        mod = _load("nsa_ops430_l", "bin/night_shift_all_products.py")
        tmp = tempfile.mkdtemp()
        spans: dict[str, tuple[float, float]] = {}

        def worker(name: str, ports: list[int]) -> None:
            with mod.port_locks(name, ports, poll_s=0.05):
                t0 = time.monotonic()
                time.sleep(0.4)
                spans[name] = (t0, time.monotonic())

        with mock.patch.dict(os.environ, {"NIGHT_SHIFT_LOCK_DIR": tmp}):
            a = threading.Thread(target=worker, args=("a", [4173]))
            b = threading.Thread(target=worker, args=("b", [4174, 4173]))
            a.start()
            time.sleep(0.05)
            b.start()
            a.join()
            b.join()
        (a0, a1), (b0, b1) = spans["a"], spans["b"]
        self.assertTrue(a1 <= b0 or b1 <= a0, spans)  # no overlap


class TestReadinessInterpreter(unittest.TestCase):
    def test_venv_python_uses_current_root_not_import_time(self):
        mod = _load("nsr_ops430", "scripts/night_shift_readiness.py")
        tmp = Path(tempfile.mkdtemp())
        py = _fake_venv(tmp)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NIGHT_SHIFT_PRODUCT_PYTHON", None)
            mod.ROOT = tmp  # what main() does for --root
            self.assertEqual(mod._venv_python(), str(py))

    def test_env_override_wins(self):
        mod = _load("nsr_ops430b", "scripts/night_shift_readiness.py")
        with mock.patch.dict(os.environ, {"NIGHT_SHIFT_PRODUCT_PYTHON": "/x/py"}):
            self.assertEqual(mod._venv_python(), "/x/py")


class TestSyncVaultSchemaLint(unittest.TestCase):
    def setUp(self):
        self.mod = _load("svsl_ops430", "scripts/sync_vault_schema_lint.py")
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "prod"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / "scripts" / "vault_schema_lint.py").write_text("# stale\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        for k, v in (("user.email", "t@example.invalid"), ("user.name", "t")):
            subprocess.run(["git", "-C", str(self.repo), "config", k, v], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "init"], check=True)
        (self.repo / "other.txt").write_text("dirty\n", encoding="utf-8")  # unrelated dirt
        self.pf = self.tmp / "products.yaml"
        self.pf.write_text(f"prod: {self.repo}\n", encoding="utf-8")

    def _run(self, *a: str) -> int:
        return self.mod.main(["--products-file", str(self.pf), *a])

    def test_check_write_idempotent_commit_only_lint(self):
        self.assertEqual(self._run("--check"), 1)
        self.assertEqual(self._run("--write", "--commit"), 0)
        tgt = self.repo / "scripts" / "vault_schema_lint.py"
        self.assertEqual(tgt.read_bytes(), self.mod.CANONICAL.read_bytes())
        files = subprocess.run(
            ["git", "-C", str(self.repo), "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
        self.assertEqual(files, ["scripts/vault_schema_lint.py"])
        mtime = tgt.stat().st_mtime_ns
        self.assertEqual(self._run("--write", "--commit"), 0)  # idempotent
        self.assertEqual(tgt.stat().st_mtime_ns, mtime)
        self.assertEqual(self._run("--check"), 0)
        self.assertTrue((self.repo / "other.txt").is_file())

    def test_staged_changes_block_commit(self):
        (self.repo / "staged.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "staged.txt"], check=True)
        self.assertEqual(self._run("--write", "--commit"), 1)
        self.assertEqual((self.repo / "scripts" / "vault_schema_lint.py").read_text(), "# stale\n")

    def test_skip_marks_stuck(self):
        self.assertEqual(self._run("--write", "--skip", "prod"), 1)
        self.assertEqual((self.repo / "scripts" / "vault_schema_lint.py").read_text(), "# stale\n")


if __name__ == "__main__":
    unittest.main()

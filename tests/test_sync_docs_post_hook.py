#!/usr/bin/env python3
"""sync_docs_full optional product post-hook (harness 1.4.47, Ops-430)."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DEPS = ("sync_docs_full.py", "sync_vault_devlog.py", "vault_resolve.py", "vault_fs.py", "product_venv.py")

HOOK = textwrap.dedent(
    """\
    import os, sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    with open(root / "hook_calls.log", "a", encoding="utf-8") as fh:
        fh.write("argv=%s env=%s ver=%s root=%s\\n" % (
            " ".join(sys.argv[1:]), os.environ.get("SYNC_DOCS_POST_HOOK", ""),
            os.environ.get("SYNC_DOCS_VERSION", ""), os.environ.get("SYNC_DOCS_ROOT", "")))
    if os.environ.get("HOOK_TEST_WRAPPER") == "1":
        # catalyxt-ds style wrapper: runs sync_docs_full itself -> must not loop
        import subprocess
        rc = subprocess.call([sys.executable, str(root / "scripts" / "sync_docs_full.py"), "--skip-vault"])
        if rc:
            sys.exit(rc)
    sys.exit(int(os.environ.get("HOOK_TEST_EXIT", "0")))
    """
)


def _load_mod():
    spec = importlib.util.spec_from_file_location("sdf_hook", ROOT / "scripts" / "sync_docs_full.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "prod"
        (self.repo / "scripts").mkdir(parents=True)
        for dep in DEPS:
            shutil.copy2(ROOT / "scripts" / dep, self.repo / "scripts" / dep)
        (self.repo / "README.md").write_text("# prod\n", encoding="utf-8")
        git = ["git", "-C", str(self.repo)]
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run([*git, "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run([*git, "config", "user.name", "t"], check=True)
        subprocess.run([*git, "add", "."], check=True)
        subprocess.run([*git, "commit", "-qm", "init"], check=True)
        subprocess.run([*git, "tag", "v9.9.9"], check=True)
        self.calls = self.repo / "hook_calls.log"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add_hook(self):
        (self.repo / "scripts" / "sync_docs_product.py").write_text(HOOK, encoding="utf-8")

    def sync(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        e = {k: v for k, v in os.environ.items() if not k.startswith(("SYNC_DOCS_", "HOOK_TEST_"))}
        e.pop("PRODUCT_VAULT_ROOT", None)
        e.update(env)
        return subprocess.run(
            [sys.executable, "scripts/sync_docs_full.py", *args],
            cwd=self.repo, env=e, capture_output=True, text=True, timeout=120, check=False,
        )

    def hook_lines(self) -> list[str]:
        return self.calls.read_text(encoding="utf-8").splitlines() if self.calls.is_file() else []


class TestPostHookEndToEnd(_Repo):
    def test_absent_hook_silent_and_ok(self):
        r = self.sync("--skip-vault")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("post-hook", r.stdout + r.stderr)
        self.assertEqual(self.hook_lines(), [])

    def test_present_hook_runs_once_with_contract(self):
        self.add_hook()
        r = self.sync("--skip-vault")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = self.hook_lines()
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("argv=--post-hook env=1 ver=v9.9.9", lines[0])
        self.assertIn(f"root={self.repo}", lines[0])
        self.assertIn("post-hook: ok", r.stdout)
        # docs sync finished before the hook
        self.assertLess(r.stdout.index("sync_docs_full complete"), r.stdout.index("post-hook:"))

    def test_failing_hook_propagates_exit(self):
        self.add_hook()
        r = self.sync("--skip-vault", HOOK_TEST_EXIT="7")
        self.assertEqual(r.returncode, 7)
        self.assertIn("❌ post-hook failed", r.stderr)
        self.assertIn("sync_docs_full complete", r.stdout)  # sync itself done

    def test_recursion_guard_wrapper_does_not_loop(self):
        self.add_hook()
        r = self.sync("--skip-vault", HOOK_TEST_WRAPPER="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.hook_lines()), 1, self.hook_lines())
        self.assertIn("SYNC_DOCS_POST_HOOK=1", r.stdout)  # inner run printed skip

    def test_guard_env_preset_skips_hook(self):
        self.add_hook()
        r = self.sync("--skip-vault", SYNC_DOCS_POST_HOOK="1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.hook_lines(), [])
        self.assertIn("post-hook: skipped", r.stdout)

    def test_dry_run_and_skip_repo_and_help_skip(self):
        self.add_hook()
        for args in (("--dry-run", "--skip-vault"), ("--skip-repo", "--skip-vault"), ("--help",)):
            r = self.sync(*args)
            self.assertEqual(r.returncode, 0, (args, r.stderr))
        self.assertEqual(self.hook_lines(), [])


class TestPostHookUnit(unittest.TestCase):
    def setUp(self):
        self.mod = _load_mod()
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "scripts").mkdir()
        (self.tmp / "scripts" / "sync_docs_product.py").write_text("", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _env(self):
        return mock.patch.dict(os.environ, {}, clear=False)

    def test_uses_product_venv_python(self):
        py = self.tmp / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True)
        py.write_text("", encoding="utf-8")
        seen = {}

        def runner(cmd, **kw):
            seen["cmd"], seen["env"] = cmd, kw["env"]
            return subprocess.CompletedProcess(cmd, 0)

        with self._env():
            os.environ.pop("SYNC_DOCS_POST_HOOK", None)
            rc = self.mod.run_post_hook(self.tmp, version="v1", runner=runner)
        self.assertEqual(rc, 0)
        self.assertEqual(seen["cmd"][0], str(py.absolute()))
        self.assertEqual(seen["cmd"][2], "--post-hook")
        self.assertEqual(seen["env"]["SYNC_DOCS_POST_HOOK"], "1")

    def test_no_venv_falls_back_to_current_interpreter(self):
        seen = {}

        def runner(cmd, **kw):
            seen["cmd"] = cmd
            return subprocess.CompletedProcess(cmd, 0)

        with self._env():
            os.environ.pop("SYNC_DOCS_POST_HOOK", None)
            self.mod.run_post_hook(self.tmp, version="v1", runner=runner)
        self.assertEqual(seen["cmd"][0], sys.executable)

    def test_timeout_is_124_and_absent_is_none(self):
        def runner(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, 1)

        with self._env():
            os.environ.pop("SYNC_DOCS_POST_HOOK", None)
            self.assertEqual(self.mod.run_post_hook(self.tmp, version="v1", runner=runner), 124)
            (self.tmp / "scripts" / "sync_docs_product.py").unlink()
            self.assertIsNone(self.mod.run_post_hook(self.tmp, version="v1", runner=runner))


if __name__ == "__main__":
    unittest.main()

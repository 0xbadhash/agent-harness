"""Open-web Chromium launch policy: refused build, sandbox flags, CDP reachability, profile ownership."""
from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "openweb_chromium_launch.py"
    spec = importlib.util.spec_from_file_location("openweb_chromium_launch", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _plan(args):
    mod = _load()
    code, argv = mod.plan_launch("Chromium 156.0.8078.79", args)
    return mod, code, argv


def _value(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


class TestOpenwebChromiumLaunch(unittest.TestCase):
    def test_refused_build_does_not_launch(self):
        mod = _load()
        code, argv = mod.plan_launch("Chromium 156.0.8078.4", ["--headless=new"])
        self.assertEqual(code, 2)
        self.assertEqual(argv, [])

    def test_newer_build_launches_without_sandbox_off_or_unconfined(self):
        mod = _load()
        code, argv = mod.plan_launch(
            "Chromium 156.0.8078.79",
            ["--headless=new", "--no-sandbox", "--disable-setuid-sandbox"],
        )
        self.assertEqual(code, 0)
        joined = " ".join(argv)
        self.assertNotIn("--no-sandbox", argv)
        self.assertNotIn("--disable-setuid-sandbox", argv)
        self.assertNotIn("apparmor=unconfined", joined)
        self.assertIn("apparmor=hermes-openweb-chromium", joined)
        self.assertIn("--headless=new", argv)


class TestCdpReachability(unittest.TestCase):
    def test_cdp_launch_joins_the_host_network(self):
        """Chromium binds DevTools to 127.0.0.1 inside its own network namespace, and it ignores
        --remote-debugging-address (measured on 156.0.8078.79), so a published port can never reach
        it. A launch that asks for a DevTools port therefore shares the host's loopback."""
        _mod, _code, argv = _plan(["--remote-debugging-port=0", "--user-data-dir=/tmp/x"])
        self.assertEqual(_value(argv, "--network"), "host")
        self.assertNotIn("-p", argv)

    def test_pipe_launch_keeps_the_isolated_bridge(self):
        """Playwright drives Chromium over a pipe: no socket to reach, so no reason to leave it."""
        _mod, _code, argv = _plan(["--remote-debugging-pipe", "--user-data-dir=/tmp/x"])
        self.assertEqual(_value(argv, "--network"), "hermes-openweb")

    def test_port_value_is_passed_through_untouched(self):
        """Chromium writes DevToolsActivePort only when it picks the port itself (=0); substituting a
        host-chosen number silently removes the file the launch waits for."""
        _mod, _code, argv = _plan(["--remote-debugging-port=0", "--user-data-dir=/tmp/x"])
        self.assertIn("--remote-debugging-port=0", argv)


class TestProfileMount(unittest.TestCase):
    def test_profile_is_mounted_at_the_same_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            _mod, _code, argv = _plan(["--remote-debugging-port=0", f"--user-data-dir={profile}"])
            self.assertEqual(_value(argv, "-v"), f"{profile}:{profile}")

    def test_planning_does_not_touch_the_filesystem(self):
        """plan_launch is a pure planner: the profile is prepared by the launch, not by argv planning."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            _plan(["--remote-debugging-port=0", f"--user-data-dir={profile}"])
            self.assertFalse(profile.exists())

    def test_profile_is_not_world_writable(self):
        """The profile holds cookies and session tokens, and the host trusts the port file inside it:
        let any local user write it and they can spoof DevToolsActivePort or plant a preferences file."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            mod._ensure_profile(str(profile), chown=lambda _path: False)
            mode = stat.S_IMODE(os.stat(profile).st_mode)
            self.assertEqual(mode & 0o022, 0, f"profile is {oct(mode)}: group/other can write it")
            self.assertTrue(mode & 0o001, "others must be able to traverse: the host reads the port file")


    def test_exec_launch_prepares_the_profile_before_handing_over(self):
        """The profile must be prepared on the executing path: Hermes creates it 0700 as its own user,
        and Chromium inside the container runs as 10001."""
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            profile.mkdir(mode=0o700)
            seen = {}

            def fake_run(argv):
                seen["argv"] = argv
                seen["mode"] = stat.S_IMODE(os.stat(profile).st_mode)
                return 0

            original = mod._chown_container_user
            mod._chown_container_user = lambda path: False  # no sudo in tests
            try:
                code = mod.exec_launch(
                    "Chromium 156.0.8078.79",
                    [f"--user-data-dir={profile}", "--remote-debugging-port=0"],
                    run=fake_run,
                )
            finally:
                mod._chown_container_user = original
            self.assertEqual(code, 0)
            self.assertEqual(seen["mode"], 0o711)
            self.assertEqual(seen["argv"][:2], ["docker", "run"])


if __name__ == "__main__":
    unittest.main()

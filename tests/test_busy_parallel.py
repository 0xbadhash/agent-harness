"""Rails for the staged busy-parallel hook. No gateway, Signal, or LLM."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from busy_parallel.decide import decide  # noqa: E402
from busy_parallel.launch import sha256_file  # noqa: E402
from busy_parallel.runner import handle  # noqa: E402


CFG = {
    "profile": "chief-of-staff",
    "max_turns": 4,
    "concurrency_cap": 2,
    "per_minute_cap": 4,
    "allow_senders": ["allowed-sender"],
    "allow_chats": ["allowed-chat"],
}


def event(**over):
    base = {
        "platform": "signal",
        "message_id": "m1",
        "text": "hello from the CEO DM",
        "message_type": "text",
        "busy": True,
        "source": {"user_id": "allowed-sender", "chat_id": "allowed-chat", "chat_type": "dm"},
    }
    base.update(over)
    return base


class Rails(unittest.TestCase):
    def setUp(self):
        self.home = Path(self.id().replace(".", "_"))
        # unique temp under /tmp
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        os.environ["HERMES_HOME"] = str(self.home)
        os.environ.pop("BUSY_PARALLEL_WORKER", None)
        os.environ.pop("BUSY_PARALLEL_MODE", None)
        os.environ.pop("BUSY_PARALLEL_KICK", None)
        (self.home / "state" / "busy-parallel").mkdir(parents=True)
        (self.home / "state" / "busy-parallel" / "ENABLE").write_text("on\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_allowlist_accept_and_reject(self):
        ok = decide(event(), CFG, self.home)
        self.assertTrue(ok.launch)
        self.assertEqual(ok.reason, "allowlist-accept")
        bad = decide(event(source={"user_id": "stranger", "chat_id": "nope", "chat_type": "dm"}), CFG, self.home)
        self.assertFalse(bad.launch)
        self.assertEqual(bad.reason, "allowlist-reject")

    def test_non_text_ignored(self):
        self.assertEqual(decide(event(message_type="image"), CFG, self.home).reason, "non-text")
        self.assertEqual(decide(event(text="  "), CFG, self.home).reason, "non-text")
        self.assertEqual(decide(event(media=True), CFG, self.home).reason, "non-text")

    def test_dedupe(self):
        first = handle(event(), self.home, CFG)
        self.assertTrue(first["launch"])
        second = handle(event(), self.home, CFG)
        self.assertFalse(second["launch"])
        self.assertEqual(second["reason"], "dedupe")

    def test_concurrency_cap(self):
        handle(event(message_id="a"), self.home, CFG)
        handle(event(message_id="b"), self.home, CFG)
        third = handle(event(message_id="c"), self.home, CFG)
        self.assertEqual(third["reason"], "concurrency-cap")

    def test_rate_cap(self):
        cfg = dict(CFG, concurrency_cap=10, per_minute_cap=2)
        handle(event(message_id="a"), self.home, cfg)
        handle(event(message_id="b"), self.home, cfg)
        third = handle(event(message_id="c"), self.home, cfg)
        self.assertEqual(third["reason"], "rate-cap")

    def test_loop_guard(self):
        self.assertEqual(decide(event(text="see [[busy-par-worker]]"), CFG, self.home).reason, "loop-guard")
        self.assertEqual(decide(event(internal=True), CFG, self.home).reason, "loop-guard")
        os.environ["BUSY_PARALLEL_WORKER"] = "1"
        self.assertEqual(decide(event(), CFG, self.home).reason, "loop-guard-process")

    def test_kill_switch(self):
        (self.home / "state" / "busy-parallel" / "ENABLE").unlink()
        self.assertEqual(decide(event(), CFG, self.home).reason, "switch-off")
        (self.home / "state" / "busy-parallel" / "ENABLE").write_text("on\n", encoding="utf-8")
        (self.home / "state" / "busy-parallel" / "DISABLED").write_text("off\n", encoding="utf-8")
        self.assertEqual(decide(event(), CFG, self.home).reason, "switch-off")

    def test_dry_run_writes_kick_and_launches_nothing(self):
        os.environ["BUSY_PARALLEL_KICK"] = "/bin/false"
        result = handle(event(), self.home, CFG)
        self.assertTrue(result["launch"])
        self.assertFalse(result["launched"])
        kick = self.home / "state" / "busy-parallel" / "jobs" / result["job_id"] / "kick.txt"
        self.assertTrue(kick.is_file())
        record = json.loads((self.home / "state" / "busy-parallel" / "would-launch" / f"{result['job_id']}.json").read_text())
        self.assertEqual(record["mode"], "dry")
        self.assertNotIn("--yolo", record["argv"])

    def test_live_calls_stub_without_yolo(self):
        stub = self.home / "fake-kick.sh"
        log = self.home / "stub-argv.txt"
        stub.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$BUSY_STUB_LOG\"\nexit 0\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        os.environ["BUSY_PARALLEL_MODE"] = "live"
        os.environ["BUSY_PARALLEL_KICK"] = str(stub)
        os.environ["BUSY_STUB_LOG"] = str(log)
        result = handle(event(message_id="live-1"), self.home, CFG)
        self.assertTrue(result["launched"])
        self.assertTrue(result["handled"])
        argv = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(argv[0], "--job-id")
        self.assertTrue(any(a.startswith("busy-par-") for a in argv))
        self.assertIn("--profile", argv)
        self.assertIn("chief-of-staff", argv)
        self.assertIn("--max-turns", argv)
        self.assertIn("4", argv)
        self.assertIn("--expect", argv)
        self.assertNotIn("--yolo", argv)
        kick = Path(argv[argv.index("--kick") + 1])
        self.assertEqual(argv[argv.index("--kick-sha") + 1], sha256_file(kick))

    def test_logs_have_no_sender_id(self):
        proc = subprocess.run(
            [sys.executable, "-m", "busy_parallel.runner"],
            input=json.dumps(event(source={"user_id": "allowed-sender", "chat_id": "allowed-chat", "chat_type": "dm"})),
            text=True,
            capture_output=True,
            cwd=str(ROOT),
            env={**os.environ, "HERMES_HOME": str(self.home), "PYTHONPATH": str(ROOT)},
            check=False,
        )
        self.assertNotIn("allowed-sender", proc.stderr)
        self.assertNotIn("allowed-chat", proc.stderr)
        self.assertNotIn("+", proc.stderr)


if __name__ == "__main__":
    unittest.main()

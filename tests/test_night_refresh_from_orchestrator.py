#!/usr/bin/env python3
"""Night job refreshes learning artifacts from reports. No autofix."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

REPORT = """# Night
**Overall:** FAIL

| Gate | Status | Exit |
| `hardcodes` | ❌ | 1 |

### hardcodes
Fix: Hardcode scan failed — remove secrets/absolute paths.
```
secret path
```
"""


def _load():
    path = ROOT / "bin" / "night_shift_all_products.py"
    spec = importlib.util.spec_from_file_location("ns_refresh_orch", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_run_one(name, root, *args, **kwargs):  # noqa: ARG001
    return {
        "name": name,
        "ok": False,
        "exit": 1,
        "root": str(root),
        "tail": "",
    }


class TestNightRefreshFromOrchestrator(unittest.TestCase):
    def test_three_artifacts_skip_autofix_exit_is_gate(self):
        mod = _load()
        sys.path.insert(0, str(ROOT / "scripts"))
        import night_fail_remediate as remediate  # noqa: E402
        import night_shift_autofix as autofix  # noqa: E402

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            root = t / "demo"
            art = root / ".agents" / "artifacts"
            art.mkdir(parents=True)
            (art / "NIGHT_SHIFT_REPORT.md").write_text(REPORT, encoding="utf-8")
            out_dir = t / "learn"
            called = {"autofix": 0, "remediate": 0}

            def boom_autofix(*args, **kwargs):  # noqa: ARG001
                called["autofix"] += 1
                raise AssertionError("attempt_autofix called")

            def boom_remediate(*args, **kwargs):  # noqa: ARG001
                called["remediate"] += 1
                raise AssertionError("remediate_product called")

            with (
                patch.object(mod, "run_one", _fake_run_one),
                patch.object(autofix, "attempt_autofix", boom_autofix),
                patch.object(remediate, "remediate_product", boom_remediate),
            ):
                code = mod.collect_and_learn(
                    [("demo", root)],
                    artifact_dir=out_dir,
                    promote=True,
                )
            self.assertEqual(code, 1)
            self.assertEqual(called["autofix"], 0)
            self.assertEqual(called["remediate"], 0)
            for name in (
                "MORNING_TRIAGE.md",
                "NIGHT_FAIL_PROMOTIONS.md",
                "NIGHT_FAIL_TICKETS.md",
            ):
                self.assertTrue((out_dir / name).is_file(), name)
            tickets = (out_dir / "NIGHT_FAIL_TICKETS.md").read_text(encoding="utf-8")
            self.assertIn("report-only; autofix not run", tickets)
            self.assertIn("gate `hardcodes`", tickets)
            self.assertIn("Hardcode scan failed — remove secrets/absolute paths.", tickets)
            self.assertNotIn("assertTrue", tickets)
            self.assertEqual(list(t.rglob("test_gate_*.py")), [])
            triage = (out_dir / "MORNING_TRIAGE.md").read_text(encoding="utf-8")
            self.assertIn("demo", triage)
            self.assertNotIn("recheck green", triage)

    def test_refresh_exception_keeps_exit_and_leaves_no_partial(self):
        mod = _load()
        sys.path.insert(0, str(ROOT / "scripts"))
        import night_shift_morning_triage as morning  # noqa: E402

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            root = t / "demo"
            art = root / ".agents" / "artifacts"
            art.mkdir(parents=True)
            (art / "NIGHT_SHIFT_REPORT.md").write_text(REPORT, encoding="utf-8")
            out_dir = t / "learn"

            def boom(results, dest):  # noqa: ARG001
                dest.write_text("partial", encoding="utf-8")
                raise RuntimeError("refresh write failed")

            with (
                patch.object(mod, "run_one", _fake_run_one),
                patch.object(morning, "write_artifact", boom),
            ):
                code = mod.collect_and_learn(
                    [("demo", root)],
                    artifact_dir=out_dir,
                )
            self.assertEqual(code, 1)
            self.assertFalse((out_dir / "MORNING_TRIAGE.md").exists())
            self.assertFalse((out_dir / "NIGHT_FAIL_PROMOTIONS.md").exists())
            self.assertFalse((out_dir / "NIGHT_FAIL_TICKETS.md").exists())
            self.assertEqual(list(out_dir.glob("*.tmp")), [])
            self.assertEqual(list(out_dir.rglob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()

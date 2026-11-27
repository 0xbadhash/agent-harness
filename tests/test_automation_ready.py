"""Automation readiness: the outer loop refuses to run on an unproven inner loop."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_automation_ready as car  # noqa: E402
import check_correction_checks as ccc  # noqa: E402
import check_lint_ratchet as clr  # noqa: E402
import check_type_ignores as cti  # noqa: E402
import night_shift_autofix as autofix  # noqa: E402


def _write_behavior(root: Path) -> None:
    path = root / car.BEHAVIOR_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# BEHAVIOR-REPORT\n\n**Marker:** BEHAVIOR-REPORT\nNEXT_SKILL=/code_review\n",
        encoding="utf-8",
    )


def _write_coverage(root: Path, percent: float = 91.5, age_hours: float = 0.0) -> None:
    path = root / car.COVERAGE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"totals": {"percent_covered": percent}}),
        encoding="utf-8",
    )
    if age_hours:
        stamp = time.time() - age_hours * 3600
        os.utime(path, (stamp, stamp))


class TestAutomationReadyCheck(unittest.TestCase):
    def _root(self, td: str) -> Path:
        root = Path(td)
        _write_behavior(root)
        _write_coverage(root)
        return root

    def test_clean_inner_loop_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            with (
                mock.patch.object(clr, "check", return_value=(True, ["ok"])),
                mock.patch.object(cti, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
            ):
                ok, messages = car.check(root, owner="0xbadhash")
            self.assertTrue(ok, messages)
            self.assertTrue(any("automation readiness proven" in m for m in messages))

    def test_missing_owner_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            with (
                mock.patch.object(clr, "check", return_value=(True, ["ok"])),
                mock.patch.object(cti, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
                mock.patch.dict(os.environ, {"AUTOMATION_OWNER": ""}),
            ):
                ok, messages = car.check(root)
            self.assertFalse(ok, messages)
            self.assertTrue(any("owner missing" in m for m in messages), messages)

    def test_owner_from_pr_draft(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            (root / "PR_DRAFT.md").write_text(
                "# Draft\n\n**Owner:** 0xbadhash\n", encoding="utf-8"
            )
            self.assertEqual(car.resolve_owner(root), "0xbadhash")

    def test_stale_coverage_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            _write_coverage(root, age_hours=48.0)
            with (
                mock.patch.object(clr, "check", return_value=(True, ["ok"])),
                mock.patch.object(cti, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
            ):
                ok, messages = car.check(root, owner="0xbadhash", max_age_hours=24.0)
            self.assertFalse(ok, messages)
            self.assertTrue(any("coverage.json is" in m for m in messages), messages)

    def test_missing_behavior_report_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            (root / car.BEHAVIOR_REL).unlink()
            with (
                mock.patch.object(clr, "check", return_value=(True, ["ok"])),
                mock.patch.object(cti, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
            ):
                ok, messages = car.check(root, owner="0xbadhash")
            self.assertFalse(ok, messages)
            self.assertTrue(any("BEHAVIOR_REPORT.md missing" in m for m in messages), messages)

    def test_missing_checker_is_named(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            with mock.patch.dict(sys.modules, {"check_lint_ratchet": None}):
                ok, messages = car.check(root, owner="0xbadhash")
            self.assertFalse(ok, messages)
            self.assertTrue(any("unavailable" in m for m in messages), messages)

    def test_failed_lint_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            with (
                mock.patch.object(clr, "check", return_value=(False, ["B904 over baseline"])),
                mock.patch.object(cti, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
            ):
                ok, messages = car.check(root, owner="0xbadhash")
            self.assertFalse(ok, messages)
            self.assertTrue(any("lint ratchet" in m for m in messages), messages)


class TestReadinessArtifact(unittest.TestCase):
    def test_roundtrip_and_freshness(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = car.write_artifact(root, "0xbadhash", ["ok: lint ratchet"])
            self.assertTrue(path.is_file())
            ok, messages = car.check_artifact(root, max_age_hours=24.0)
            self.assertTrue(ok, messages)

            stamp = time.time() - 48 * 3600
            os.utime(path, (stamp, stamp))
            ok, messages = car.check_artifact(root, max_age_hours=24.0)
            self.assertFalse(ok, messages)
            self.assertTrue(any("is" in m and "old" in m for m in messages), messages)

    def test_missing_artifact_fails(self):
        with tempfile.TemporaryDirectory() as td:
            ok, messages = car.check_artifact(Path(td))
            self.assertFalse(ok, messages)

    def test_artifact_recording_failure_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = car.write_artifact(root, "0xbadhash", ["fail: lint ratchet — worse"])
            self.assertTrue(path.is_file())
            ok, messages = car.check_artifact(root)
            self.assertFalse(ok, messages)
            self.assertTrue(any("failed check" in m for m in messages), messages)


class TestAutofixReadinessGate(unittest.TestCase):
    def _failed(self) -> list[dict]:
        return [{"name": "product_smoke", "ok": False, "stdout_tail": "", "stderr_tail": ""}]

    def test_outer_loop_blocked_without_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(autofix, "try_ensure_dev_env") as ensure:
                attempts = autofix.attempt_autofix(
                    root, self._failed(), require_readiness=True
                )
            self.assertEqual(len(attempts), 1, attempts)
            self.assertEqual(attempts[0]["name"], "autofix_blocked")
            self.assertFalse(attempts[0]["ok"])
            ensure.assert_not_called()

    def test_outer_loop_runs_with_current_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            car.write_artifact(root, "0xbadhash", ["ok: lint ratchet"])
            with mock.patch.object(
                autofix,
                "try_ensure_dev_env",
                return_value={"name": "ensure_dev_env", "ok": False},
            ) as ensure:
                attempts = autofix.attempt_autofix(
                    root, self._failed(), require_readiness=True
                )
            self.assertTrue(any(a["name"] == "ensure_dev_env" for a in attempts), attempts)
            ensure.assert_called_once()

    def test_gate_off_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(
                autofix,
                "try_ensure_dev_env",
                return_value={"name": "ensure_dev_env", "ok": False},
            ) as ensure:
                attempts = autofix.attempt_autofix(root, self._failed())
            ensure.assert_called_once()
            self.assertFalse(any(a["name"] == "autofix_blocked" for a in attempts))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tier A/B/C ship coverage for agent-harness 1.4.28.

AC map: AC-1 AC-2 AC-3 AC-4 AC-5 AC-6 AC-7 AC-8 AC-9 AC-10
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_compatibility  # noqa: E402
import check_harness_manifest  # noqa: E402
import check_mcp_contract  # noqa: E402
import check_pi_fixtures  # noqa: E402
import check_sbom_signing  # noqa: E402
import evidence_hash  # noqa: E402
import protect_sot_merge  # noqa: E402
import recovery_demo  # noqa: E402
import telemetry_emit  # noqa: E402
from check_secrets_diff import main as secrets_main  # noqa: E402


class TestTierA(unittest.TestCase):
    def test_ac_1_manifest_ok(self):
        ok, msgs = check_harness_manifest.check(ROOT / "harness.manifest.yaml")
        self.assertTrue(ok, msgs)

    def test_ac_2_compatibility_ok(self):
        ok, msgs = check_compatibility.check(ROOT)
        self.assertTrue(ok, msgs)

    def test_ac_3_critical_list_nonempty(self):
        rels = protect_sot_merge._load_list(ROOT / "config" / "critical_sot_scripts.txt")
        self.assertGreaterEqual(len(rels), 5)

    def test_ac_4_scanner_strict_env(self):
        with mock.patch("check_secrets_diff.run_gitleaks", return_value=(-1, "")):
            with mock.patch(
                "check_secrets_diff.run_trufflehog", return_value=(-1, "")
            ):
                with mock.patch.dict(os.environ, {"SCANNER_STRICT": "1"}):
                    rc = secrets_main(["--repo", str(ROOT)])
        self.assertEqual(rc, 1)


class TestTierB(unittest.TestCase):
    def test_ac_5_mcp_contract_ok(self):
        ok, _ = check_mcp_contract.check(ROOT)
        self.assertTrue(ok)

    def test_ac_8_pi_fixtures(self):
        ok, msgs = check_pi_fixtures.check(ROOT)
        self.assertTrue(ok, msgs)

    def test_ac_6_recovery_demo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ok, msgs = recovery_demo.demo(root)
            self.assertTrue(ok, msgs)
            self.assertTrue((root / ".agents" / "artifacts" / "RECOVERY_DEMO.md").is_file())

    def test_ac_7_evidence_hash(self):
        rows = evidence_hash.collect(ROOT)
        self.assertTrue(any(d for _, d in rows))

    def test_ac_9_github_daytime_module(self):
        import github_daytime_status as gds  # noqa: E402

        md = gds.render_markdown(
            [{"product": "agent-harness", "repo": "0xbadhash/agent-harness", "status": "success", "branch": "main", "url": ""}]
        )
        self.assertIn("daytime-gates", md)


class TestTierC(unittest.TestCase):
    def test_ac_10_sbom_warn_ok(self):
        ok, _ = check_sbom_signing.check(ROOT, strict=False)
        self.assertTrue(ok)

    def test_sbom_strict_may_fail(self):
        # harness may only have docs/signing.md now
        ok, msgs = check_sbom_signing.check(ROOT, strict=True)
        self.assertTrue(ok, msgs)  # docs/signing.md present

    def test_telemetry_off_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("HARNESS_TELEMETRY", None)
                p = telemetry_emit.emit(Path(td), "test", {"k": "v"})
                self.assertIsNone(p)

    def test_telemetry_on(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"HARNESS_TELEMETRY": "1"}):
                p = telemetry_emit.emit(Path(td), "test", {"k": "v"})
                self.assertIsNotNone(p)
                self.assertTrue(p.is_file())

    def test_ac_10_non_goal_in_manifest(self):
        text = (ROOT / "harness.manifest.yaml").read_text(encoding="utf-8")
        self.assertIn("multi-agent-runtime", text)
        self.assertIn("non_goals:", text)


if __name__ == "__main__":
    unittest.main()

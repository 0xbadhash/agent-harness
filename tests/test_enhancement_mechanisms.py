"""Unit proofs for the E01-E25 enhancement mechanisms (offline, deterministic).

The frozen acceptance suite in ``tests/enhancement_specs/`` asserts the end
state. These tests exercise the behavior behind each marker so a regression in
the mechanism, not just a missing string, fails the suite.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_comment_audit as cca  # noqa: E402
import check_compact_safety as ccs  # noqa: E402
import check_lint_ratchet as clr  # noqa: E402
import check_pr_body as cpb  # noqa: E402
import cross_review_gate as crg  # noqa: E402
import fork_sync_bot as fsb  # noqa: E402
import gate_conventions as gc  # noqa: E402
import night_shift_readiness as nsr  # noqa: E402
import prototype_variants as pv  # noqa: E402
import research_report as rr  # noqa: E402
import retro_job as rj  # noqa: E402
import smart_zone_guard as szg  # noqa: E402
import spec_gate as sg  # noqa: E402
import waiver_report as wr  # noqa: E402
import wizard  # noqa: E402


class TestGateConventions(unittest.TestCase):
    def test_spec_and_waiver_parsing(self):
        self.assertEqual(gc.spec_path("**Spec:** .agents/specs/x.md"), ".agents/specs/x.md")
        self.assertEqual(gc.waiver_type("**Spec waiver:** docs-only"), "docs-only")
        self.assertTrue(gc.is_waiver("**Spec waiver:** prose-only"))
        self.assertIsNone(gc.waiver_type("no waiver here"))


class TestPrBodyGate(unittest.TestCase):
    BODY = (
        "## Smallest visual change\n"
        "The smallest slice: one route now returns the new header.\n\n"
        "## Before/after\n"
        "Before: `curl -i` returned 500. After: it returns 200 with `x-new: 1`.\n\n"
        "## Merge danger\n"
        "Two-way: revert the commit and the old response returns.\n"
    )

    def test_complete_body_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text(self.BODY, encoding="utf-8")
            ok, msgs = cpb.check(root)
            self.assertTrue(ok, msgs)

    def test_missing_merge_danger_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            body = self.BODY.split("## Merge danger")[0]
            (root / "PR_DRAFT.md").write_text(body, encoding="utf-8")
            ok, msgs = cpb.check(root)
            self.assertFalse(ok)
            self.assertIn("Merge danger", "\n".join(msgs))

    def test_docs_only_waiver_skips(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text("**Spec waiver:** docs-only\n", encoding="utf-8")
            ok, _ = cpb.check(root)
            self.assertTrue(ok)


class TestLintRatchet(unittest.TestCase):
    def test_ratchet_only_fails_on_increase(self):
        self.assertTrue(clr.compare({"E1": 2}, {"E1": 2})[0])
        ok, msgs = clr.compare({"E1": 1}, {"E1": 2})
        self.assertTrue(ok)
        self.assertIn("improved", "\n".join(msgs))
        ok, msgs = clr.compare({"E1": 3}, {"E1": 2})
        self.assertFalse(ok)
        self.assertIn("baseline", "\n".join(msgs))


class TestCrossReviewAxes(unittest.TestCase):
    def test_standards_axis_flags_bare_except(self):
        with mock.patch.object(
            crg, "_added_lines", return_value=[("scripts/x.py", "except:")]
        ):
            result = crg.review_standards("HEAD~1...HEAD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["axis"], "standards")

    def test_standards_axis_clean(self):
        with mock.patch.object(
            crg, "_added_lines", return_value=[("scripts/x.py", "except ValueError:")]
        ):
            result = crg.review_standards("HEAD~1...HEAD")
        self.assertTrue(result["ok"], result)

    def test_spec_axis_traces_acceptance_criteria(self):
        # Build the id at runtime so this test file does not itself satisfy the
        # trace when review_spec_fidelity scans tests/ for AC references.
        ac_id = "AC-" + "987" + "654"
        with tempfile.TemporaryDirectory() as td:
            spec = Path(td) / "spec.md"
            spec.write_text(f"- [ ] {ac_id} is met\n", encoding="utf-8")
            with mock.patch.object(
                crg, "_added_lines", return_value=[("scripts/x.py", f"handles {ac_id}")]
            ):
                ok_result = crg.review_spec_fidelity("HEAD~1...HEAD", spec)
            with mock.patch.object(crg, "_added_lines", return_value=[("scripts/x.py", "unrelated")]):
                bad_result = crg.review_spec_fidelity("HEAD~1...HEAD", spec)
        self.assertTrue(ok_result["ok"], ok_result)
        self.assertFalse(bad_result["ok"])
        self.assertEqual(bad_result["axis"], "spec-fidelity")


class TestRetroJob(unittest.TestCase):
    def test_clusters_findings_by_lesson(self):
        clusters = rj.cluster_lessons(
            [
                ("CODE_REVIEW.md", "missing regression test for the parser"),
                ("CROSS_REVIEW.md", "spec AC-3 was not traced to a test"),
            ]
        )
        self.assertIn("tests", clusters)
        self.assertIn("spec", clusters)

    def test_writes_a_retro_from_disk_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifacts = root / ".agents" / "artifacts"
            artifacts.mkdir(parents=True)
            (artifacts / "CODE_REVIEW.md").write_text(
                "- missing regression test for the parser\n", encoding="utf-8"
            )
            text = rj.build_retro(root, datetime(2026, 11, 22, tzinfo=UTC))
            self.assertIn("## Clusters", text)
            self.assertIn("tests", text)
            path = rj.write_retro(root, text, root / "docs" / "retros" / "r.md")
            self.assertTrue(path.is_file())


class TestCommentAudit(unittest.TestCase):
    def test_flags_history_code_and_ownerless_todo(self):
        # Split so check_repo_hygiene does not flag this fixture as an orphan TODO.
        ownerless_todo = "# " + "TODO: fix this\n"
        findings = cca.audit_text(
            "x = 1\n"
            "# previously this returned None\n"
            "# def old(): pass\n"
            + ownerless_todo
            + "# TODO(alice): rewrite parser\n"
        )
        kinds = "\n".join(findings)
        self.assertIn("history", kinds)
        self.assertIn("commented_code", kinds)
        self.assertEqual(sum("todo" in item for item in findings), 1)

    def test_owned_todo_is_clean(self):
        self.assertIsNone(cca.classify_comment("# TODO(alice): rewrite parser"))


class TestSmartZone(unittest.TestCase):
    def test_boundary_and_plan(self):
        self.assertEqual(szg.zone_state(szg.SMART_ZONE_TOKENS), "inside")
        self.assertEqual(szg.zone_state(szg.SMART_ZONE_TOKENS + 1), "externalize")
        plan = "\n".join(szg.externalization_plan(szg.SMART_ZONE_TOKENS + 1))
        self.assertIn("externalize", plan)
        self.assertIn("fresh", plan)


class TestCompactSafety(unittest.TestCase):
    def test_blocks_without_spec_tickets_glossary(self):
        with tempfile.TemporaryDirectory() as td:
            ok, msgs = ccs.check(Path(td))
        self.assertFalse(ok)
        text = "\n".join(msgs).lower()
        self.assertIn("spec", text)
        self.assertIn("ticket", text)
        self.assertIn("glossary", text)

    def test_passes_when_artifacts_are_on_disk(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".agents" / "specs").mkdir(parents=True)
            (root / ".agents" / "specs" / "x.md").write_text("# Spec\n", encoding="utf-8")
            (root / "tickets").mkdir()
            (root / "tickets" / "01-a.md").write_text(
                "**depends_on:** None\n", encoding="utf-8"
            )
            (root / "GLOSSARY.md").write_text("# GLOSSARY\n", encoding="utf-8")
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** .agents/specs/x.md\n**Tickets:** tickets\n", encoding="utf-8"
            )
            ok, msgs = ccs.check(root)
        self.assertTrue(ok, msgs)


class TestPrototypeVariants(unittest.TestCase):
    def test_writes_two_to_three_disposable_variants(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            written = pv.make_variants("TTL or write generation?", slug="cache", root=root)
            self.assertEqual(len(written), 3)
            bodies = [p.read_text(encoding="utf-8") for p in written]
            self.assertTrue(all("DO NOT SHIP" in body for body in bodies))
            self.assertEqual(len({body.split("**Lens:**")[1] for body in bodies}), 3)
            written = pv.make_variants("q", slug="few", variants=9, root=root)
            self.assertEqual(len(written), 3)


class TestWizard(unittest.TestCase):
    def test_wizard_is_an_executable_runbook(self):
        text = wizard.build_wizard(
            "DNS cutover",
            ["Create the A record", "Wait for TTL"],
            prerequisites=["Console access"],
        )
        for needed in ("**Owner:**", "## Preconditions", "## Steps", "## Verify", "## Rollback"):
            self.assertIn(needed, text)
        self.assertIn("1. [ ] Create the A record", text)


class TestResearchReport(unittest.TestCase):
    NOTES = (
        "Intro prose is not a claim.\n\n"
        "- The suite did not run, so the gate read green. "
        "[evidence](https://example.test/ci/1)\n\n"
        "- Missing tools folded into skip.\n"
        "  Source: scripts/night_shift_readiness.py\n\n"
        "- A bullet without any citation.\n"
    )

    def test_claims_require_sources(self):
        claims = rr.parse_claims(self.NOTES)
        self.assertEqual(len(claims), 3)
        self.assertEqual(rr.uncited(claims), ["A bullet without any citation."])
        report = rr.build_report("Why?", claims)
        self.assertIn("⚠️ MISSING", report)

    def test_strict_refuses_uncited_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            notes = root / "notes.md"
            notes.write_text(self.NOTES, encoding="utf-8")
            rc = rr.main(
                [
                    "--question",
                    "Why did drift stay silent?",
                    "--notes",
                    str(notes),
                    "--root",
                    str(root),
                    "--strict",
                ]
            )
            self.assertEqual(rc, 1)
            self.assertFalse((root / "docs" / "research").exists())
            rc = rr.main(
                [
                    "--question",
                    "Why did drift stay silent?",
                    "--notes",
                    str(notes),
                    "--root",
                    str(root),
                    "--slug",
                    "drift",
                ]
            )
            self.assertEqual(rc, 0)
            written = list((root / "docs" / "research").glob("*-drift.md"))
            self.assertEqual(len(written), 1)
            self.assertIn("Source: scripts/night_shift_readiness.py", written[0].read_text())


class TestForkSyncBot(unittest.TestCase):
    def test_parses_counts_and_builds_issue_body(self):
        divergence = fsb.parse_counts("2\t3\n")
        self.assertEqual((divergence.ahead, divergence.behind), (2, 3))
        self.assertTrue(divergence.diverged)
        body = fsb.issue_body(divergence)
        self.assertRegex(body, r"issue")
        self.assertIn("ahead: 2", body)
        self.assertIn("behind: 3", body)
        self.assertIn("fork drift", fsb.issue_title(divergence))

    def test_divergence_uses_git_counts(self):
        calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "4\t5\n", "")

        with tempfile.TemporaryDirectory() as td:
            divergence = fsb.git_divergence(Path(td), runner=fake_run)
        self.assertEqual((divergence.ahead, divergence.behind), (4, 5))
        self.assertIn("origin/main...main", " ".join(calls[0]))

    def test_git_failure_raises(self):
        def fake_run(cmd, cwd):
            return subprocess.CompletedProcess(cmd, 1, "", "unknown revision")

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                fsb.git_divergence(Path(td), runner=fake_run)

    def test_create_calls_gh_issue(self):
        calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "https://example.test/issues/1\n", "")

        with tempfile.TemporaryDirectory() as td:
            fsb.open_issue("title", "body", repo="o/r", root=Path(td), runner=fake_run)
        self.assertEqual(calls[0][:4], ["gh", "issue", "create", "--title"])
        self.assertIn("--repo", calls[0])


class TestWaiverClusters(unittest.TestCase):
    def test_groups_by_gate_and_type(self):
        rows = [
            {"gate": "spec_gate", "waiver_type": "hotfix"},
            {"gate": "spec_gate", "waiver_type": "hotfix"},
            {"gate": "spec_gate", "waiver_type": "hotfix"},
            {"gate": "hard_gates", "waiver_type": "chore"},
        ]
        clusters = wr.cluster_waivers(rows)
        self.assertEqual(len(clusters[("spec_gate", "hotfix")]), 3)
        self.assertEqual(len(clusters[("hard_gates", "chore")]), 1)


class TestNightShiftVerdicts(unittest.TestCase):
    def test_degraded_and_red_suite_are_distinct(self):
        self.assertEqual(nsr.overall_verdict([{"ok": True}]), "PASS")
        self.assertEqual(nsr.overall_verdict([{"ok": False}]), "FAIL")
        self.assertEqual(nsr.overall_verdict([{"ok": False, "status": "DEGRADED"}]), "DEGRADED")
        red = nsr.red_suite_result("tests", "suite did not run")
        self.assertEqual(red["status"], "RED_SUITE")
        self.assertEqual(nsr.overall_verdict([{"ok": True}, red]), "RED_SUITE")
        both = [{"ok": False, "status": "DEGRADED"}, red]
        self.assertEqual(nsr.overall_verdict(both), "DEGRADED")


class TestSpecGateAdditions(unittest.TestCase):
    def test_repro_required_for_bug_specs(self):
        ok, _ = sg.check_repro_requirement("**Type:** bug\n")
        self.assertFalse(ok)
        spec = (
            "**Type:** bug\n\n## Reproduction\n"
            "Repro: `pytest -k x` failed with exit 1 before the fix.\n"
        )
        ok, msgs = sg.check_repro_requirement(spec)
        self.assertTrue(ok, msgs)
        ok, _ = sg.check_repro_requirement("**Type:** feature\n")
        self.assertTrue(ok)

    def test_ticket_blocking_edges_resolve_and_reject_cycles(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tickets = root / "tickets"
            tickets.mkdir()
            spec = root / ".agents" / "specs" / "x.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("**Tickets:** tickets\n", encoding="utf-8")
            (tickets / "01-a.md").write_text("**depends_on:** None\n", encoding="utf-8")
            (tickets / "02-b.md").write_text("**depends_on:** 01-a.md\n", encoding="utf-8")
            ok, msgs = sg.check_ticket_blocking_edges(root, spec, spec.read_text())
            self.assertTrue(ok, msgs)

            (tickets / "01-a.md").write_text("**depends_on:** 02-b.md\n", encoding="utf-8")
            (tickets / "02-b.md").write_text("**depends_on:** 01-a.md\n", encoding="utf-8")
            ok, msgs = sg.check_ticket_blocking_edges(root, spec, spec.read_text())
            self.assertFalse(ok)
            self.assertIn("cycle", "\n".join(msgs))


if __name__ == "__main__":
    unittest.main()

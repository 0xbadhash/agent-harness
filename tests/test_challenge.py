"""Challenge script: fake models, temporary vault. No live API."""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import challenge  # noqa: E402


class ChallengeTests(unittest.TestCase):
    def test_pass_writes_artifact_and_vault(self) -> None:
        # isolate under tmp via TemporaryDirectory
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "product"
            vault = Path(tmp) / "vault"
            (root / ".agents").mkdir(parents=True)
            plugin = root / ".agents" / "product_plugin.yaml"
            plugin.write_text(
                "vault:\n  enabled: true\n  project_label: demo\n",
                encoding="utf-8",
            )
            proposal = Path(tmp) / "proposal.md"
            proposal.write_text("Allow INDEX.md.\n", encoding="utf-8")
            decision = Path(tmp) / "decision.md"
            decision.write_text("Allow it, and add a stray-file test.\n", encoding="utf-8")

            def glm(prompt: str) -> str:
                return "glm:" + prompt[:12]

            def deepseek(prompt: str) -> str:
                return "ds:" + prompt[:12]

            code = challenge.main(
                ["--proposal", str(proposal), "--decision", str(decision), "--root", str(root), "--vault", str(vault)],
                glm=glm,
                deepseek=deepseek,
            )
            self.assertEqual(code, 0)
            artifact = (root / ".agents" / "artifacts" / "CHALLENGE.md").read_text(encoding="utf-8")
            self.assertIn("Allow it, and add a stray-file test.", artifact)
            notes = list((vault / "01-Projects" / "demo" / "challenges").glob("*.md"))
            self.assertEqual(len(notes), 1)
            self.assertIn("stray-file test", notes[0].read_text(encoding="utf-8"))
            decisions = (vault / "01-Projects" / "demo" / "decisions.md").read_text(encoding="utf-8")
            self.assertIn("challenges/", decisions)

    def test_one_model_down_leaves_vault_unchanged(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "product"
            vault = Path(tmp) / "vault"
            root.mkdir()
            vault.mkdir()
            (root / ".agents" / "product_plugin.yaml").parent.mkdir(parents=True)
            (root / ".agents" / "product_plugin.yaml").write_text(
                "vault:\n  enabled: true\n  project_label: demo\n",
                encoding="utf-8",
            )
            marker = vault / "01-Projects" / "demo" / "keep.txt"
            marker.parent.mkdir(parents=True)
            marker.write_text("untouched\n", encoding="utf-8")
            before = marker.read_bytes()
            proposal = Path(tmp) / "proposal.md"
            proposal.write_text("Proposal.\n", encoding="utf-8")

            def glm(_prompt: str) -> str:
                raise challenge.ModelError("GLM failed")

            def deepseek(prompt: str) -> str:
                return "ds " + prompt[:8]

            code = challenge.main(
                ["--proposal", str(proposal), "--root", str(root), "--vault", str(vault)],
                glm=glm,
                deepseek=deepseek,
            )
            self.assertEqual(code, 1)
            self.assertFalse((root / ".agents" / "artifacts" / "CHALLENGE.md").exists())
            self.assertEqual(marker.read_bytes(), before)
            self.assertFalse((vault / "01-Projects" / "demo" / "challenges").exists())



    def test_braces_in_proposal_and_critiques_are_not_format_fields(self) -> None:
        """Braces are ordinary text: a proposal naming ``{render_page,capture}.py`` or a critique that
        quotes code used to crash the note with ``KeyError`` because the rendered body was fed back
        through ``str.format``."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "product"
            root.mkdir()
            proposal = Path(tmp) / "proposal.md"
            proposal.write_text("Scripts {render_page,capture}.py need a resolver.\n", encoding="utf-8")
            decision = Path(tmp) / "decision.md"
            decision.write_text("Accept; keep {a,b} as literals.\n", encoding="utf-8")

            code = challenge.main(
                ["--proposal", str(proposal), "--decision", str(decision), "--root", str(root),
                 "--vault", str(Path(tmp) / "vault")],
                glm=lambda prompt: "glm says {x}",
                deepseek=lambda prompt: "ds says {y}",
            )

            self.assertEqual(code, 0)
            body = (root / ".agents" / "artifacts" / "CHALLENGE.md").read_text(encoding="utf-8")
            self.assertIn("{render_page,capture}", body)
            self.assertIn("{a,b}", body)
            self.assertIn("glm says {x}", body)
            self.assertIn("ds says {y}", body)

    def test_unset_vault_refuses_instead_of_host_default(self) -> None:
        """No --vault and no PRODUCT_VAULT_ROOT must not fall back to /opt/second-brain.

        That fallback, plus the label ``product``, is how a fixture wrote
        ``01-Projects/product/`` into the live vault.
        """
        import tempfile

        saved = os.environ.pop("PRODUCT_VAULT_ROOT", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "widget"
                root.mkdir()
                with self.assertRaises(ValueError):
                    challenge._vault_paths(root, "slug", None)
        finally:
            if saved is not None:
                os.environ["PRODUCT_VAULT_ROOT"] = saved


if __name__ == "__main__":
    unittest.main()


class ChallengePreflightTests(unittest.TestCase):
    """A missing vault must cost zero model calls, not four."""

    def test_unset_vault_calls_no_model(self) -> None:
        import challenge

        calls: list[str] = []

        def glm(_prompt: str) -> str:
            calls.append("glm")
            raise AssertionError("glm must not be called during pre-flight")

        def deepseek(_prompt: str) -> str:
            calls.append("deepseek")
            raise AssertionError("deepseek must not be called during pre-flight")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proposal = root / "p.md"
            proposal.write_text("# proposal\n\nbody\n", encoding="utf-8")
            decision = root / "d.md"
            decision.write_text("# decision\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                rc = challenge.main(["--proposal", str(proposal), "--decision", str(decision),
                                     "--root", str(root)], glm=glm, deepseek=deepseek)
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])

    def test_check_flag_calls_no_model(self) -> None:
        import challenge

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proposal = root / "p.md"
            proposal.write_text("# proposal\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = challenge.main(["--proposal", str(proposal), "--root", str(root),
                                     "--vault", str(root), "--check"],
                                    glm=lambda _p: (_ for _ in ()).throw(AssertionError("no model")),
                                    deepseek=lambda _p: (_ for _ in ()).throw(AssertionError("no model")))
        self.assertEqual(rc, 0)
        self.assertIn("note:", out.getvalue())


class ChallengeVaultExistsTests(unittest.TestCase):
    def test_nonexistent_vault_calls_no_model(self) -> None:
        import challenge

        calls: list[str] = []

        def boom(_prompt: str) -> str:
            calls.append("model")
            raise AssertionError("no model call may happen when the vault path is wrong")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proposal = root / "p.md"
            proposal.write_text("# proposal\n", encoding="utf-8")
            decision = root / "d.md"
            decision.write_text("# decision\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                locked = root / "ro"
                locked.mkdir()
                locked.chmod(0o500)
                try:
                    rc = challenge.main(["--proposal", str(proposal), "--decision", str(decision),
                                         "--root", str(root), "--vault", str(locked / "vault")],
                                        glm=boom, deepseek=boom)
                finally:
                    locked.chmod(0o700)
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])

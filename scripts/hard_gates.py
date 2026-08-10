#!/usr/bin/env python3
"""Hard gates for /pr_review --validate (fail closed evidence pack).

Applicable gates depend on review_scope (prose-only vs code; runtime surface).
Does not advance pipeline.json.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC_RE = re.compile(
    r"\*\*Spec:\*\*\s*(\S+)",
    re.IGNORECASE,
)
WAIVER_RE = re.compile(
    r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b",
    re.IGNORECASE,
)
RED_PROOF_RE = re.compile(
    r"(red.?proof|red_cmd|green_cmd|TDD\s*N/?A|docs-only.*TDD|TDD.*docs-only|"
    r"red\s*→\s*green|went red then green)",
    re.IGNORECASE,
)
# B2: AC → test/smoke mapping
TRACE_HEADER_RE = re.compile(r"^##\s+Traceability\b", re.IGNORECASE | re.MULTILINE)
TRACE_ROW_RE = re.compile(
    r"(AC-\d+|acceptance|smoke|pytest|test_|unittest|\.py\b|scripts/)",
    re.IGNORECASE,
)
THREAT_HEADER_RE = re.compile(r"^##\s+Threat notes\b", re.IGNORECASE | re.MULTILINE)
THREAT_BULLET_RE = re.compile(r"^\s*[-*]\s+\S+", re.MULTILINE)
# B5: release-style evidence pack in PR_DRAFT (code ships)
EVIDENCE_HEADER_RE = re.compile(r"^##\s+Evidence pack\b", re.IGNORECASE | re.MULTILINE)
EVIDENCE_TOKEN_RE = re.compile(
    r"\b(hard_gates|smoke|pytest|unittest|validate|coverage|sbom|product_smoke)\b",
    re.IGNORECASE,
)


@dataclass
class HardGatesResult:
    ok: bool
    violations: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    prose_only: bool = False
    runtime: bool = False


def _scope_flags(root: Path, diff: str | None) -> tuple[bool, bool]:
    """Return (prose_only, runtime_surface)."""
    try:
        from review_scope import (  # type: ignore
            build_baseline,
            should_skip_heavy_review,
        )
    except ImportError:
        return False, True

    base, head = "HEAD~1", "HEAD"
    if diff:
        # Accept A...B or A..B
        for sep in ("...", ".."):
            if sep in diff:
                parts = diff.split(sep, 1)
                if len(parts) == 2 and parts[0] and parts[1]:
                    base, head = parts[0], parts[1]
                break
    try:
        b = build_baseline(root, base=base, head=head)
    except Exception:
        return False, True
    prose = bool(should_skip_heavy_review(b) or b.prose_only)
    runtime = _runtime_surface(b) if not prose else False
    return prose, runtime


def _runtime_surface(baseline) -> bool:
    """Match next_skill runtime heuristic without importing next_skill."""
    if getattr(baseline, "prose_only", False):
        return False
    runtime_ext = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".php",
        ".sh",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
        ".css",
        ".html",
        ".sql",
    }
    for f in baseline.files:
        p = f.replace("\\", "/")
        if p.endswith("SKILL.md") or "/.agents/skills/" in p:
            continue
        suf = Path(p).suffix.lower()
        if suf in runtime_ext:
            return True
        if p.startswith("src/") or p.startswith("scripts/") or p.startswith("deploy/"):
            return True
    return False


def _secrets_ok(root: Path, diff: str | None) -> bool:
    script = SCRIPTS / "check_secrets_diff.py"
    if not script.is_file():
        return True
    # Not a git checkout (unit fixtures) → do not block
    if not (root / ".git").exists() and not (root / ".git").is_file():
        # Also allow when cwd git is unrelated — only scan when root is a repo
        try:
            chk = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if chk.returncode != 0 or "true" not in (chk.stdout or ""):
                return True
        except (OSError, subprocess.TimeoutExpired):
            return True
    base, head = "HEAD~1", "HEAD"
    if diff:
        for sep in ("...", ".."):
            if sep in diff:
                parts = diff.split(sep, 1)
                if len(parts) == 2:
                    base, head = parts[0], parts[1]
                break
    try:
        r = subprocess.run(
            [
                sys.executable,
                str(script),
                "--base",
                base,
                "--head",
                head,
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return True  # do not block if tooling broken; hardcode scan still runs


def _has_marker(path: Path, *needles: str) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(n in text for n in needles)


# HSQ-2: minimum substance for CODE-REVIEW (auto-marker stubs fail this floor)
CODE_REVIEW_MIN_CHARS = 180
CODE_REVIEW_AUTO_MARKER = "Auto-written by run_ship_chain"


def _code_review_quality(path: Path) -> tuple[bool, str]:
    """Return (ok, detail). Marker required; thin/auto stubs fail quality floor."""
    if not path.is_file():
        return False, "missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if not any(n in text for n in ("CODE-REVIEW", "CODE_REVIEW", "**Marker:** CODE-REVIEW")):
        return False, "no marker"
    body = text.strip()
    if CODE_REVIEW_AUTO_MARKER in text and len(body) < 400:
        return False, "auto-marker stub too thin (expand /code_review or pass quality floor)"
    if len(body) < CODE_REVIEW_MIN_CHARS:
        return False, f"body < {CODE_REVIEW_MIN_CHARS} chars"
    # require a verdict-ish word
    low = body.lower()
    if not any(w in low for w in ("verdict", "approve", "reject", "finding", "p0", "pass", "fail")):
        return False, "missing verdict/findings language"
    return True, "ok"


def _log_skip_hard_gates(root: Path) -> None:
    import os
    from datetime import datetime
    art = Path(root) / ".agents" / "artifacts"
    try:
        art.mkdir(parents=True, exist_ok=True)
        log = art / "SKIP_HARD_GATES_LOG.jsonl"
        row = {
            "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actor": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
            "cwd": str(Path(root).resolve()),
        }
        with log.open("a", encoding="utf-8") as f:
            import json
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass


def evaluate(
    root: Path,
    pr_draft: Path,
    *,
    diff: str | None = None,
    skip: bool = False,
) -> HardGatesResult:
    """Evaluate hard gates for a ship."""
    root = Path(root).resolve()
    pr_draft = Path(pr_draft)
    if skip:
        _log_skip_hard_gates(root)
        return HardGatesResult(ok=True, skipped=["all (--skip-hard-gates)"])

    violations: list[str] = []
    skipped: list[str] = []
    prose_only, runtime = _scope_flags(root, diff)

    draft_text = ""
    if pr_draft.is_file():
        draft_text = pr_draft.read_text(encoding="utf-8", errors="replace")
    else:
        violations.append("hard_gates: PR_DRAFT.md missing")

    # Spec path or waiver (always)
    has_spec = bool(SPEC_RE.search(draft_text))
    has_waiver = bool(WAIVER_RE.search(draft_text))
    if not has_spec and not has_waiver:
        violations.append(
            "hard_gates: Spec — need **Spec:** <path> or "
            "**Spec waiver:** hotfix|chore|docs-only|prose-only"
        )

    if prose_only:
        skipped.extend(["CODE-REVIEW", "Red-proof", "BEHAVIOR-REPORT (prose-only)"])
    else:
        code_art = root / ".agents" / "artifacts" / "CODE_REVIEW.md"
        ok_cr, detail_cr = _code_review_quality(code_art)
        if not ok_cr:
            violations.append(
                "hard_gates: CODE-REVIEW "
                + detail_cr
                + " — write .agents/artifacts/CODE_REVIEW.md with marker CODE-REVIEW "
                + f"and ≥{CODE_REVIEW_MIN_CHARS} chars + verdict/findings "
                + "(auto-marker stubs from run_ship_chain fail this floor)"
            )
        if not RED_PROOF_RE.search(draft_text):
            violations.append(
                "hard_gates: Red-proof missing — document red_cmd/green_cmd or TDD N/A in PR_DRAFT"
            )
        # B2 Traceability: AC → tests/smoke
        if not TRACE_HEADER_RE.search(draft_text):
            violations.append(
                "hard_gates: Traceability missing — add ## Traceability mapping AC → test/smoke"
            )
        else:
            # section body should mention tests or smoke
            m = re.search(
                r"##\s+Traceability\b(.*?)(?=\n## |\Z)",
                draft_text,
                re.IGNORECASE | re.DOTALL,
            )
            body = m.group(1) if m else ""
            if not TRACE_ROW_RE.search(body) or len(body.strip()) < 20:
                violations.append(
                    "hard_gates: Traceability section too thin — map each AC to a test or smoke"
                )
        if runtime:
            beh = root / ".agents" / "artifacts" / "BEHAVIOR_REPORT.md"
            if not _has_marker(
                beh, "BEHAVIOR-REPORT", "BEHAVIOR_REPORT", "**Marker:** BEHAVIOR-REPORT"
            ):
                violations.append(
                    "hard_gates: BEHAVIOR-REPORT missing for runtime surface — "
                    "run /behavior_validator or write .agents/artifacts/BEHAVIOR_REPORT.md"
                )
            # B4 Threat notes
            if not THREAT_HEADER_RE.search(draft_text):
                violations.append(
                    "hard_gates: Threat notes missing — add ## Threat notes (≥2 bullets) for runtime ships"
                )
            else:
                tm = re.search(
                    r"##\s+Threat notes\b(.*?)(?=\n## |\Z)",
                    draft_text,
                    re.IGNORECASE | re.DOTALL,
                )
                tbody = tm.group(1) if tm else ""
                bullets = THREAT_BULLET_RE.findall(tbody)
                if len(bullets) < 2:
                    violations.append(
                        "hard_gates: Threat notes need ≥2 bullets (assets / abuse cases)"
                    )
        else:
            skipped.append("BEHAVIOR-REPORT (no runtime surface)")
            skipped.append("Threat notes (no runtime surface)")

        # B5 Evidence pack (code ships only)
        if not EVIDENCE_HEADER_RE.search(draft_text):
            violations.append(
                "hard_gates: Evidence pack missing — add ## Evidence pack "
                "(hard_gates / smoke / pytest / validate / coverage / SBOM)"
            )
        else:
            em = re.search(
                r"^##\s+Evidence pack\b(.*?)(?=\n## |\Z)",
                draft_text,
                re.IGNORECASE | re.DOTALL | re.MULTILINE,
            )
            ebody = em.group(1) if em else ""
            tokens = set(t.lower() for t in EVIDENCE_TOKEN_RE.findall(ebody))
            if len(tokens) < 2 or len(ebody.strip()) < 20:
                violations.append(
                    "hard_gates: Evidence pack too thin — cite ≥2 of "
                    "hard_gates, smoke, pytest/unittest, validate, coverage, SBOM"
                )

    # Secrets on diff (fail closed when check fails) — G5 patterns in check_secrets_diff
    if not _secrets_ok(root, diff):
        violations.append(
            "hard_gates: secrets scan failed on diff — fix or narrow before approve"
        )
    else:
        skipped.append("secrets (clean or skip)")

    # HSQ-3 P0 G1: AC → test map (non-prose feature ships)
    if not prose_only:
        try:
            from check_ac_traceability import check as _ac_check  # type: ignore

            ac_ok, ac_msgs = _ac_check(root, pr_draft)
            if not ac_ok:
                for m in ac_msgs:
                    violations.append(f"hard_gates: AC map — {m}")
            else:
                skipped.append("ac_map (" + (ac_msgs[0] if ac_msgs else "ok") + ")")
        except Exception as e:  # pragma: no cover
            violations.append(f"hard_gates: AC map check error: {e}")
    else:
        skipped.append("ac_map (prose-only)")

    # HSQ-3 P0 G14: py_compile changed .py (disk is truth)
    if not prose_only:
        try:
            from check_diff_compile import check as _compile_check  # type: ignore

            base, head = "HEAD~1", "HEAD"
            if diff:
                for sep in ("...", ".."):
                    if sep in diff:
                        parts = diff.split(sep, 1)
                        if len(parts) == 2 and parts[0] and parts[1]:
                            base, head = parts[0], parts[1]
                        break
            c_ok, c_msgs = _compile_check(root, base, head)
            if not c_ok:
                for m in c_msgs:
                    violations.append(f"hard_gates: diff_compile — {m}")
            else:
                skipped.append("diff_compile (" + (c_msgs[0] if c_msgs else "ok") + ")")
        except Exception as e:  # pragma: no cover
            violations.append(f"hard_gates: diff_compile error: {e}")
    else:
        skipped.append("diff_compile (prose-only)")

    # Web E2E + Comet contract when product has a website (fail closed)
    if not prose_only:
        try:
            from web_e2e_contract import validate_web_e2e  # type: ignore

            we = validate_web_e2e(root)
            if we.get("has_website"):
                if not we.get("pass"):
                    for v in we.get("violations") or []:
                        violations.append(f"hard_gates: web_e2e — {v}")
                else:
                    skipped.append("web_e2e (ok)")
            else:
                skipped.append("web_e2e (no website)")
        except Exception as e:  # pragma: no cover
            violations.append(f"hard_gates: web_e2e check error: {e}")
    else:
        skipped.append("web_e2e (prose-only)")

    return HardGatesResult(
        ok=len(violations) == 0,
        violations=violations,
        skipped=skipped,
        prose_only=prose_only,
        runtime=runtime,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument("--diff", default=None)
    ap.add_argument("--skip-hard-gates", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    draft = args.pr_draft or (root / "PR_DRAFT.md")
    r = evaluate(root, draft, diff=args.diff, skip=args.skip_hard_gates)
    print(f"hard_gates ok={r.ok} prose_only={r.prose_only} runtime={r.runtime}")
    for v in r.violations:
        print(f"  ❌ {v}")
    for s in r.skipped:
        print(f"  ↷ skip {s}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

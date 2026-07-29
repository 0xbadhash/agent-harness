#!/usr/bin/env python3
"""Print a single mandatory handoff line: NEXT_SKILL=...

Used by execute_dev / code_review / cross_review / behavior_validator so agents
and humans always know the exact next slash skill.

Examples::

  python3 scripts/next_skill.py --after execute_dev --base HEAD~1 --head HEAD
  python3 scripts/next_skill.py --after code_review --base origin/main
  python3 scripts/next_skill.py --after behavior_validator

Exit 0 always when it can decide; prints exactly one NEXT_SKILL= line to stdout
(plus optional KEY= notes on stderr for humans).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from review_scope import (  # noqa: E402
    build_baseline,
    is_large_baseline,
    should_skip_heavy_review,
)


def _large(baseline, repo: Path | None = None) -> bool:
    """Shared review_scope thresholds (files / churn / non_test_loc / product paths)."""
    product_n = 0
    prefixes_configured = False
    if repo is not None:
        try:
            from product_plugin import (  # type: ignore
                load_product_path_prefixes,
                path_matches_product_prefixes,
            )

            prefixes = load_product_path_prefixes(Path(repo).resolve())
            prefixes_configured = bool(prefixes)
            if prefixes:
                product_n = sum(
                    1
                    for f in baseline.files
                    if path_matches_product_prefixes(f, prefixes)
                )
        except Exception:  # noqa: BLE001
            pass
    large, _ = is_large_baseline(
        baseline,
        product_path_count=product_n,
        product_prefixes_configured=prefixes_configured,
    )
    return large


def _runtime_surface(baseline) -> bool:
    """Heuristic: code/config that could affect running product."""
    if baseline.prose_only:
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


def _strip_yaml_comments(text: str) -> str:
    """Drop full-line and trailing # comments (not inside simple quotes)."""
    out: list[str] = []
    for line in text.splitlines():
        s = line
        in_s = in_d = False
        cut = len(s)
        for i, ch in enumerate(s):
            if ch == "'" and not in_d:
                in_s = not in_s
            elif ch == '"' and not in_s:
                in_d = not in_d
            elif ch == "#" and not in_s and not in_d:
                cut = i
                break
        out.append(s[:cut])
    return "\n".join(out)


def _infra_required(repo: Path) -> bool:
    """True only when this product needs /vps_infra_ops before release.

    Required when the product ships the skill, or product_plugin declares infra.
    Portable harness products without either skip straight to /release_mgmt.
    """
    root = Path(repo).resolve()
    for rel in (
        ".agents/skills/vps_infra_ops/SKILL.md",
        "skills/vps_infra_ops/SKILL.md",
        ".grok/skills/vps_infra_ops/SKILL.md",
    ):
        if (root / rel).is_file():
            return True
    plugin = root / ".agents" / "product_plugin.yaml"
    if not plugin.is_file():
        return False
    try:
        text = plugin.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    # Prefer structured plugin keys when PyYAML (or minimal parse) is available
    try:
        from product_plugin import load_plugin  # type: ignore

        data = load_plugin(root)
        if data:
            if data.get("require_vps_infra") in (True, "true", "yes", "1", 1):
                return True
            if data.get("vps_infra") in (True, "true", "yes", "1", 1):
                return True
            if data.get("vps_infra_ops") in (True, "true", "yes", "1", 1):
                return True
            infra = data.get("infra")
            if isinstance(infra, dict) and infra.get("required") in (
                True,
                "true",
                "yes",
                "1",
                1,
            ):
                return True
            if infra in (True, "true", "yes", "required"):
                return True
    except Exception:  # noqa: BLE001 — fall through to text scan
        pass

    # Text scan ignores comments so `# require_vps_infra: true` is not a hit
    low = _strip_yaml_comments(text).lower()
    compact = "".join(low.split())
    for needle in (
        "require_vps_infra:true",
        "require_vps_infra:yes",
        "vps_infra:true",
        "vps_infra_ops:true",
        "infra:required:true",
    ):
        if needle in compact:
            return True
    # Block form:
    #   infra:
    #     required: true
    if "infra:" in low:
        idx = low.find("infra:")
        chunk = low[idx : idx + 200]
        if "required: true" in chunk or "required:true" in chunk.replace(" ", ""):
            return True
    return False


def decide(
    after: str,
    *,
    base: str,
    head: str,
    repo: Path,
    force_cross: bool = False,
    skip_behavior: bool = False,
    skip_infra: bool = False,
    skip_qa: bool = False,
) -> tuple[str, dict[str, str]]:
    """Return (next_skill_token, meta).

    Raises ValueError when ``after`` is empty/whitespace-only.
    """
    after = (after or "").strip().lstrip("/").replace("-", "_")
    if not after:
        raise ValueError("empty --after; pass the skill that just finished")
    meta: dict[str, str] = {"after": after}

    if after == "behavior_validator":
        return "/pr_review --validate", {**meta, "reason": "behavior done"}

    if after == "pr_review":
        # Only suggest vps_infra when product requires it; else release.
        if not skip_infra and _infra_required(repo):
            return "/vps_infra_ops --verify", {
                **meta,
                "reason": "approved path: infra required for this product",
                "infra": "required",
            }
        return "/release_mgmt", {
            **meta,
            "reason": "if approved → release (infra not required); if blocked → execute_dev",
            "infra": "skipped",
        }

    if after in ("vps_infra_ops", "vps_infra"):
        return "/release_mgmt", {
            **meta,
            "reason": "infra verify done (or N/A) → release",
        }

    if after == "release_mgmt":
        return "/sync_docs", {**meta, "reason": "after shipped"}

    if after == "sync_docs":
        # After full FSM: suggest deep QA (esp. large releases). Optional; not a phase.
        if skip_qa:
            return "(done)", {
                **meta,
                "reason": "cycle complete → init (qa_campaign skipped)",
                "qa": "skipped",
            }
        return "/qa_campaign", {
            **meta,
            "reason": "full FSM complete → optional deep QA / bug-hunt campaign",
            "qa": "suggested",
        }

    if after in ("qa_campaign", "qa-campaign", "full_qa", "e2e_qa"):
        return "(done)", {
            **meta,
            "reason": "QA campaign finished (or skipped) → idle",
        }

    if after == "handoff":
        return "(continue with task)", {**meta, "reason": "handoff is not a ship step"}

    if after in ("session_viewer", "agent_transcript"):
        return "(return to ship path)", {**meta, "reason": "ops skill; resume execute_dev or pr_review"}

    # Only these skills need a diff baseline to choose the next step
    _needs_scope = {"execute_dev", "code_review", "cross_review"}
    if after not in _needs_scope:
        # Unknown after: do not invent a ship step — signal clearly for agents.
        return "(unknown after; re-run with ship skill)", {
            **meta,
            "reason": "unknown after=; not a known ship step",
        }

    try:
        b = build_baseline(repo, base=base, head=head)
    except Exception as exc:  # noqa: BLE001
        # Fail open to safe default for *known* review steps only
        meta["scope_error"] = str(exc)
        if after == "execute_dev":
            return "/code_review", meta
        return "/pr_review --validate", meta

    meta["prose_only"] = str(b.prose_only)
    meta["large"] = str(_large(b, repo))
    meta["runtime"] = str(_runtime_surface(b))
    meta["n_files"] = str(b.n_files)

    if after == "execute_dev":
        if should_skip_heavy_review(b):
            # Small internal docs: skip code_review and cross_review
            return "/pr_review --validate", {
                **meta,
                "reason": "prose-only → skip code_review",
                "code_review": "skipped",
            }
        return "/code_review", {**meta, "reason": "non-prose code ship", "code_review": "required"}

    if after == "code_review":
        if force_cross or _large(b, repo):
            return "/cross_review", {**meta, "reason": "large/non-trivial diff"}
        if not skip_behavior and _runtime_surface(b):
            return "/behavior_validator", {
                **meta,
                "reason": "runtime surface → behavior contract check",
            }
        return "/pr_review --validate", {**meta, "reason": "small code; score next"}

    # cross_review
    if not skip_behavior and _runtime_surface(b):
        return "/behavior_validator", {
            **meta,
            "reason": "runtime surface after personas",
        }
    return "/pr_review --validate", {**meta, "reason": "no runtime surface or behavior skipped"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--after",
        required=True,
        help="Skill just finished: execute_dev|code_review|cross_review|behavior_validator|…",
    )
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument(
        "--force-cross",
        action="store_true",
        help="After code_review, always choose cross_review",
    )
    ap.add_argument(
        "--skip-behavior",
        action="store_true",
        help="Never route to behavior_validator",
    )
    ap.add_argument(
        "--skip-infra",
        action="store_true",
        help="After pr_review, never route to /vps_infra_ops even if product has it",
    )
    ap.add_argument(
        "--skip-qa",
        action="store_true",
        help="After sync_docs, do not suggest /qa_campaign (print NEXT_SKILL=(done))",
    )
    ap.add_argument("--verbose", action="store_true", help="Print meta on stderr")
    args = ap.parse_args(argv)

    try:
        nxt, meta = decide(
            args.after,
            base=args.base,
            head=args.head,
            repo=args.repo.resolve(),
            force_cross=args.force_cross,
            skip_behavior=args.skip_behavior,
            skip_infra=args.skip_infra,
            skip_qa=args.skip_qa,
        )
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        print("NEXT_SKILL=(error: empty --after)")
        return 2

    # Exactly one handoff line for agents/humans to parse
    print(f"NEXT_SKILL={nxt}")
    if args.verbose:
        for k, v in sorted(meta.items()):
            print(f"# {k}={v}", file=sys.stderr)
    # Non-zero when after was unknown so automation does not follow garbage
    if meta.get("reason", "").startswith("unknown after"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Spec gate for /execute_dev — require Spec path or Spec waiver before code work.

Exit 0 = ok; 1 = blocked.
Reads PR_DRAFT.md and optional pipeline.json fields (spec_id, waiver).

HSQ-1: successful waivers append one JSON line to
``.agents/artifacts/WAIVER_LOG.jsonl`` (append-only ledger).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gate_conventions import (  # noqa: E402
    SPEC_MARKER,
    SPEC_RE,
    WAIVER_MARKER,
    WAIVER_RE,
    WAIVERS,
)

# E13: an ADR is worth recording only when the decision is hard to reverse,
# surprising to a reader, or carries a real tradeoff. A section that states
# none of the three is spec theater.
ADR_HEADER_RE = re.compile(
    r"^##+\s+(?:ADR(?:[-\s]\d+)?|Decision record)\b", re.IGNORECASE | re.MULTILINE
)
REVERSIBLE_RE = re.compile(r"reversib", re.IGNORECASE)
SURPRISE_RE = re.compile(r"surpris", re.IGNORECASE)
TRADEOFF_RE = re.compile(r"trade[-\s]?off", re.IGNORECASE)

# E14: uppercase domain terms in the spec must resolve in GLOSSARY.md.
UPPER_TERM_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}\b")
GLOSSARY_ALLOW = frozenset(
    {
        "AC", "ADR", "API", "CI", "CLI", "JSON", "HTTP", "HTTPS", "LLM", "N/A",
        "PDF", "PR", "README", "TDD", "TODO", "UI", "URL", "UX", "UUID", "YAML",
    }
)
GLOSSARY_PATHS = ("GLOSSARY.md", "docs/GLOSSARY.md")

# E16: tickets carry blocking edges so the build order is explicit.
TICKETS_LINE_RE = re.compile(r"\*\*Tickets:\*\*\s*(\S+)", re.IGNORECASE)
DEPENDS_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?(?:Blocked by|depends_on|blocked_by)\s*:?(?:\*\*)?\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)

# E20: a bug fix needs a reproduction that went red before the fix.
BUG_SIGNAL_RE = re.compile(
    r"^\*\*(?:Type|Kind):\*\*\s*bug\b|^#+\s+Bug\b", re.IGNORECASE | re.MULTILINE
)
REPRO_HEADER_RE = re.compile(
    r"^##+\s+(?:Repro(?:duction)?)\b", re.IGNORECASE | re.MULTILINE
)

# E23/E24: a spec names which decisions are the operator's and which are
# delegated, and a user-visible ship names its feature flag.
RESERVED_RE = re.compile(r"\*\*Reserved decisions:\*\*\s*(\S.+)", re.IGNORECASE)
DELEGATED_RE = re.compile(r"\*\*Delegated decisions:\*\*\s*(\S.+)", re.IGNORECASE)
FLAG_RE = re.compile(r"\*\*Feature flag:\*\*\s*(\S.+)", re.IGNORECASE)
SURFACE_RE = re.compile(r"\*\*Surface:\*\*\s*user-visible", re.IGNORECASE)


def _pipeline(root: Path) -> dict:
    p = root / ".agents" / "state" / "pipeline.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _git_sha(root: Path) -> str:
    r = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return ""


def append_waiver_log(
    root: Path,
    *,
    waiver_type: str,
    spec_id: str = "",
    reason: str = "",
    gate: str = "spec_gate",
) -> Path | None:
    """Append one waiver record. Returns log path or None on failure."""
    root = Path(root).resolve()
    art = root / ".agents" / "artifacts"
    try:
        art.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    log = art / "WAIVER_LOG.jsonl"
    pipe = _pipeline(root)
    product_id = ""
    try:
        from product_plugin import load_plugin

        plugin = load_plugin(root)
        product_id = str(plugin.get("product_id") or root.name)
    except Exception:  # noqa: BLE001
        product_id = root.name
    row = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "product_id": product_id,
        "waiver_type": waiver_type,
        "gate": gate,
        "spec_id": spec_id or None,
        "pipeline_phase": pipe.get("phase"),
        "actor": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        "git_sha": _git_sha(root),
        "reason": reason or None,
    }
    try:
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        return None
    return log


def _section_body(text: str, header: re.Pattern[str]) -> str:
    match = header.search(text)
    if not match:
        return ""
    tail = text[match.end() :]
    nxt = re.search(r"^##+\s", tail, re.MULTILINE)
    return tail[: nxt.start()] if nxt else tail


def check_adr_three_part(text: str) -> tuple[bool, list[str]]:
    """E13 — ADR sections must answer reversible / surprise / tradeoff."""
    if not ADR_HEADER_RE.search(text):
        return True, ["ok: no ADR section — three-part test N/A"]
    body = _section_body(text, ADR_HEADER_RE)
    missing = [
        label
        for label, pattern in (
            ("reversibility", REVERSIBLE_RE),
            ("surprise", SURPRISE_RE),
            ("tradeoff", TRADEOFF_RE),
        )
        if not pattern.search(body)
    ]
    if missing:
        return False, [
            "ADR three-part test: missing "
            + ", ".join(missing)
            + " — say whether the decision is reversible, what would surprise "
            "a reader, and the tradeoff; drop the ADR if none apply"
        ]
    return True, ["ok: ADR three-part test (reversibility / surprise / tradeoff)"]


def _glossary_entries(root: Path) -> tuple[list[tuple[str, int]], Path | None]:
    """Return (term, line_number) pairs from the first glossary file found."""
    for rel in GLOSSARY_PATHS:
        path = root / rel
        if not path.is_file():
            continue
        entries: list[tuple[str, int]] = []
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            row = line.strip()
            if row.startswith("|") and not row.startswith("|---"):
                cells = [c.strip() for c in row.strip("|").split("|")]
                if cells and cells[0] and cells[0].lower() != "term":
                    entries.append((re.sub(r"[`*]", "", cells[0]).strip(), number))
            elif row.startswith(("-", "*")):
                match = re.match(r"^[-*]\s+\*\*([^*]+)\*\*", row)
                if match:
                    entries.append((match.group(1).strip(), number))
        return entries, path
    return [], None


def _glossary_terms(root: Path) -> tuple[set[str], Path | None]:
    entries, path = _glossary_entries(root)
    return {term for term, _ in entries}, path


def _collision_key(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", term.lower())


def check_glossary(root: Path, text: str) -> tuple[bool, list[str]]:
    """E14 — uppercase domain terms must be defined in GLOSSARY.md."""
    terms, path = _glossary_terms(Path(root))
    if path is None:
        return True, ["ok: no GLOSSARY.md — domain-term check N/A"]
    known = {t.lower() for t in terms}
    undefined = sorted(
        {
            term
            for term in UPPER_TERM_RE.findall(text)
            if term not in GLOSSARY_ALLOW and term.lower() not in known
        }
    )
    if undefined:
        return False, [
            f"undefined domain term(s) {', '.join(undefined)} — add each to "
            f"{path.relative_to(root)} with a one-line definition"
        ]
    return True, [f"ok: domain terms resolved in {path.relative_to(root)}"]


def check_glossary_collisions(root: Path) -> tuple[bool, list[str]]:
    """E14b — two rows must not define the same normalized term."""
    entries, path = _glossary_entries(Path(root))
    if path is None:
        return True, ["ok: no GLOSSARY.md — collision check N/A"]
    seen: dict[str, tuple[str, int]] = {}
    collisions: list[str] = []
    for term, number in entries:
        key = _collision_key(term)
        if not key:
            continue
        if key in seen and seen[key][0] != term:
            first, first_line = seen[key]
            collisions.append(
                f"{path.name}:{first_line} {first!r} collides with "
                f"{path.name}:{number} {term!r} (normalized {key!r})"
            )
        else:
            seen.setdefault(key, (term, number))
    if collisions:
        return False, ["glossary collision(s): " + "; ".join(collisions)]
    return True, [f"ok: {len(entries)} glossary term(s), no normalized collisions"]


def _ticket_dir(root: Path, spec_path: Path, text: str) -> Path | None:
    match = TICKETS_LINE_RE.search(text)
    if match:
        raw = match.group(1).strip().strip("`")
        candidate = (root / raw).resolve()
        if candidate.is_dir() and str(candidate).startswith(str(root.resolve())):
            return candidate
        return None
    sibling = spec_path.parent / spec_path.stem / "tickets"
    return sibling if sibling.is_dir() else None


def check_ticket_blocking_edges(
    root: Path, spec_path: Path, text: str
) -> tuple[bool, list[str]]:
    """E16 — each ticket declares blocking edges that resolve to other tickets."""
    tickets_dir = _ticket_dir(root, spec_path, text)
    if tickets_dir is None:
        return True, ["ok: no tickets dir — blocking-edge check N/A"]
    tickets = sorted(tickets_dir.glob("*.md"))
    if not tickets:
        return False, [f"tickets dir empty: {tickets_dir.relative_to(root)}"]
    ids = {p.stem for p in tickets}
    short_ids: dict[str, str] = {}
    for ticket in tickets:
        short_ids.setdefault(re.split(r"[-_.]", ticket.stem)[0], ticket.stem)
    failures: list[str] = []
    graph: dict[str, set[str]] = {}
    for ticket in tickets:
        body = ticket.read_text(encoding="utf-8", errors="replace")
        edges = DEPENDS_RE.findall(body)
        if not edges:
            failures.append(
                f"{ticket.name}: missing **Blocked by:** / depends_on edge "
                "(use 'None' for a root ticket)"
            )
            continue
        deps: set[str] = set()
        for raw in edges:
            for token in re.split(r"[,\s]+", raw.strip()):
                token = token.strip("`[]()").rstrip(".")
                if not token or token.lower() in {"none", "n/a", "na", "-", "none."}:
                    continue
                stem = token[:-3] if token.lower().endswith(".md") else token
                target = stem if stem in ids else short_ids.get(stem)
                if target is None:
                    failures.append(f"{ticket.name}: blocking edge {token!r} has no ticket")
                elif target == ticket.stem:
                    failures.append(f"{ticket.name}: ticket blocks itself")
                else:
                    deps.add(target)
        graph[ticket.stem] = deps

    state: dict[str, int] = {}

    def _cycle(node: str) -> bool:
        state[node] = 1
        for dep in graph.get(node, set()):
            if state.get(dep, 0) == 1:
                return True
            if state.get(dep, 0) == 0 and _cycle(dep):
                return True
        state[node] = 2
        return False

    for ticket_id in sorted(graph):
        if state.get(ticket_id, 0) == 0 and _cycle(ticket_id):
            failures.append(f"{ticket_id}: blocking edges form a cycle")
            break
    if failures:
        return False, failures
    return True, [f"ok: {len(tickets)} ticket(s) with blocking edges"]


def check_repro_requirement(text: str) -> tuple[bool, list[str]]:
    """E20 — a bug-fix spec needs a reproduction that failed first."""
    if not BUG_SIGNAL_RE.search(text):
        return True, ["ok: not a bug fix — repro requirement N/A"]
    if not REPRO_HEADER_RE.search(text):
        return False, [
            "bug fix requires a ## Reproduction section: the command or steps "
            "that failed before the change, and the observed red result"
        ]
    body = _section_body(text, REPRO_HEADER_RE)
    if not re.search(r"repro", body, re.IGNORECASE) or not re.search(
        r"\b(red|fail|error|traceback|exit\s*[1-9])\b", body, re.IGNORECASE
    ):
        return False, [
            "## Reproduction must name a repro command/steps and the red result "
            "(error, traceback, or non-zero exit) observed before the fix"
        ]
    return True, ["ok: bug-fix reproduction recorded (went red first)"]


def check_decision_record(text: str) -> tuple[bool, list[str]]:
    """E23 — write down which decisions are reserved and which are delegated."""
    reserved = RESERVED_RE.search(text)
    delegated = DELEGATED_RE.search(text)
    msgs: list[str] = []
    if reserved is None:
        msgs.append(
            "warn: missing **Reserved decisions:** — state the choices only the "
            "operator may make"
        )
    if delegated is None:
        msgs.append(
            "warn: missing **Delegated decisions:** — state the choices the agent "
            "may make without asking"
        )
    if reserved and delegated:
        msgs.append("ok: reserved and delegated decisions recorded")
    return True, msgs


def check_feature_flag(text: str) -> tuple[bool, list[str]]:
    """E24 — a user-visible ship names the flag that can turn it off."""
    if SURFACE_RE.search(text) is None:
        return True, ["ok: no user-visible surface declared — feature-flag check N/A"]
    match = FLAG_RE.search(text)
    value = match.group(1).strip().lower() if match else ""
    if not value or value in {"none", "-", "n/a", "na"}:
        return False, [
            "user-visible ship needs **Feature flag:** <name> and an off-path, "
            "or **Surface:** internal when there is no user-visible change"
        ]
    return True, [f"ok: feature flag named ({value[:60]})"]


def check(
    root: Path,
    *,
    pr_draft: Path | None = None,
    allow_missing_draft: bool = False,
    log_waiver: bool = True,
) -> tuple[bool, list[str]]:
    """Return (ok, messages)."""
    root = Path(root).resolve()
    draft_path = pr_draft or (root / "PR_DRAFT.md")
    msgs: list[str] = []
    draft = ""
    if draft_path.is_file():
        draft = draft_path.read_text(encoding="utf-8", errors="replace")
    elif not allow_missing_draft:
        # pipeline-only path still allowed
        pass

    pipe = _pipeline(root)
    waiver = (pipe.get("waiver") or "").strip().lower()
    spec_id = (pipe.get("spec_id") or "").strip()

    m = SPEC_RE.search(draft)
    w = WAIVER_RE.search(draft)
    if w:
        waiver = w.group(1).lower()
    if m:
        spec_id = m.group(1).strip().strip("`")

    if waiver in WAIVERS:
        msgs.append(f"ok: Spec waiver={waiver}")
        if log_waiver:
            path = append_waiver_log(root, waiver_type=waiver, spec_id=spec_id)
            if path:
                msgs.append(f"ok: waiver logged → {path.relative_to(root)}")
        return True, msgs

    if spec_id:
        # Relative to product root
        cand = root / spec_id
        spec_path: Path | None = None
        if cand.is_file():
            spec_path = cand
        elif Path(spec_id).is_file():
            spec_path = Path(spec_id)
        if spec_path is None:
            msgs.append(f"fail: Spec path not found: {spec_id}")
            return False, msgs
        msgs.append(f"ok: Spec file {spec_id}")
        # Grill-me evidence (mandatory for feature Specs; skip only on Spec waiver above)
        try:
            from check_spec_grill import check_path as _grill_check

            g_ok, g_msgs = _grill_check(spec_path)
            msgs.extend(g_msgs)
            if not g_ok:
                return False, msgs
        except Exception as e:  # noqa: BLE001
            msgs.append(f"fail: grill check error: {e}")
            return False, msgs

        spec_text = spec_path.read_text(encoding="utf-8", errors="replace")
        for checker, args in (
            (check_adr_three_part, (spec_text,)),
            (check_glossary, (root, spec_text)),
            (check_ticket_blocking_edges, (root, spec_path, spec_text)),
            (check_repro_requirement, (spec_text,)),
            (check_decision_record, (spec_text,)),
            (check_feature_flag, (spec_text,)),
        ):
            c_ok, c_msgs = checker(*args)
            msgs.extend(c_msgs)
            if not c_ok:
                return False, msgs

        c_ok, c_msgs = check_glossary_collisions(root)
        msgs.extend(c_msgs)
        if not c_ok:
            return False, msgs
        if draft:
            f_ok, f_msgs = check_feature_flag(draft)
            msgs.extend(f_msgs)
            if not f_ok:
                return False, msgs
        return True, msgs

    msgs.append(
        f"fail: need {SPEC_MARKER} <path> in PR_DRAFT or pipeline spec_id, "
        f"or {WAIVER_MARKER} hotfix|chore|docs-only|prose-only"
    )
    return False, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument(
        "--allow-missing-draft",
        action="store_true",
        help="Allow pipeline-only spec_id/waiver without PR_DRAFT",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Treat warn: lines (reserved/delegated decisions) as failures",
    )
    args = ap.parse_args(argv)
    ok, msgs = check(
        args.root,
        pr_draft=args.pr_draft,
        allow_missing_draft=args.allow_missing_draft,
    )
    if ok and args.strict and any(m.startswith("warn:") for m in msgs):
        ok = False
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m if not m.startswith("ok:") and not m.startswith("fail:") else ("✅ " + m[4:] if m.startswith("ok:") else "❌ " + m[6:]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

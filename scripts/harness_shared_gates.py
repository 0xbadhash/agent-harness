#!/usr/bin/env python3
"""Gate primitives owned by THIS repo (E35, integrated per-repo by CEO ruling).

agent-harness keeps its own copy of the evidence hash, the run-record schema
and the one-way-door gate. workflow-harness keeps an equivalent copy in
framework/shared.py; a box-only consistency check in tests/enhancement_specs
keeps the two copies from drifting (same primitive names, same schema version).
No external package is imported here: a fresh checkout of this repo works
on its own.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Mapping

# ---------------------------------------------------------------------------
# One-way-door gates
# ---------------------------------------------------------------------------


class GateRefused(PermissionError):
    """A one-way door was opened without the stamp it requires."""


@dataclass(frozen=True)
class Stamp:
    """A named human's approval, with the evidence that they gave it."""

    by: str
    stamp: str
    at: str

    @classmethod
    def parse(cls, value: "Stamp | Mapping | None") -> "Stamp | None":
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(by=str(value.get("by") or ""), stamp=str(value.get("stamp") or ""),
                       at=str(value.get("at") or ""))
        return None

    def problems(self) -> list[str]:
        out: list[str] = []
        if not self.by.strip():
            out.append("stamp has no name: a stamp must name the human who gave it")
        if not self.stamp.strip():
            out.append("stamp has no evidence id")
        if not self.at.strip():
            out.append("stamp has no timestamp")
        return out


@dataclass(frozen=True)
class Gate:
    """A step that may or may not be reversible."""

    name: str
    one_way: bool = True
    stamp_owner: str = "CEO"

    def check(self, stamp: "Stamp | Mapping | None") -> tuple[bool, list[str]]:
        if not self.one_way:
            return True, []
        parsed = Stamp.parse(stamp)
        if parsed is None:
            return False, [f"{self.name} is a one-way door and needs the {self.stamp_owner} stamp"]
        problems = parsed.problems()
        if parsed.by.strip().casefold() != self.stamp_owner.casefold():
            problems.append(
                f"{self.name} needs the {self.stamp_owner} stamp; got {parsed.by or 'nobody'}"
            )
        return (not problems), problems


def require(gate: Gate, stamp: "Stamp | Mapping | None") -> None:
    ok, problems = gate.check(stamp)
    if not ok:
        raise GateRefused("; ".join(problems))


# ---------------------------------------------------------------------------
# Evidence: hash a path, then re-hash it to prove the chain
# ---------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    """Digest a file without loading it whole: run records can point at PDFs."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


@dataclass(frozen=True)
class EvidenceCheck:
    row: int
    step: str
    path: str | None
    expected: str | None
    actual: str | None
    ok: bool
    reason: str = ""


@dataclass
class ChainReport:
    checks: list[EvidenceCheck] = field(default_factory=list)
    skipped: int = 0

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def failures(self) -> list[EvidenceCheck]:
        return [c for c in self.checks if not c.ok]

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "checked": len(self.checks),
            "skipped": self.skipped,
            "failures": [
                {"row": c.row, "step": c.step, "path": c.path, "reason": c.reason}
                for c in self.failures
            ],
        }


def _resolve(raw: str, root: Path | None) -> Path:
    p = Path(raw).expanduser()
    if p.is_absolute():
        return p
    return (root or Path.cwd()) / p


def verify_evidence_chain(
    rows: Iterable[Mapping],
    *,
    root: str | Path | None = None,
    require_hash: bool = True,
) -> ChainReport:
    """Re-hash every `evidence_path` in a run record.

    Rows without an evidence path are counted as skipped: a model call with no
    artefact is legitimate. Rows that name a path must carry a digest that
    matches it, otherwise the audit trail is a claim, not evidence.
    """
    base = Path(root) if root is not None else None
    report = ChainReport()
    for index, row in enumerate(rows):
        raw = row.get("evidence_path")
        if not raw:
            report.skipped += 1
            continue
        step = str(row.get("step") or "?")
        path = _resolve(str(raw), base)
        expected = row.get("evidence_sha256")
        if not path.exists():
            report.checks.append(EvidenceCheck(index, step, str(raw), expected, None, False,
                                               "evidence path does not exist"))
            continue
        if path.is_dir():
            report.checks.append(EvidenceCheck(index, step, str(raw), expected, None, False,
                                               "evidence path is a directory, not an artefact"))
            continue
        actual = sha256_file(path)
        if expected is None:
            report.checks.append(EvidenceCheck(index, step, str(raw), None, actual, not require_hash,
                                               "no evidence_sha256 recorded"))
            continue
        report.checks.append(EvidenceCheck(
            index, step, str(raw), str(expected), actual, str(expected) == actual,
            "" if str(expected) == actual else "digest mismatch: the artefact changed after it was recorded",
        ))
    return report


# ---------------------------------------------------------------------------
# Run-record rules
# ---------------------------------------------------------------------------

SCHEMA_VERSION = 2

REQUIRED_FIELDS = ("run_id", "workflow", "item", "step", "status", "started", "ended", "duration_s")

# schema v1 (before 2026-11-22) had no schema_version. A reader that meets such
# a line must treat it as v1 rather than reject it: old evidence stays readable.
MIGRATION_NOTES = {
    1: "rows written before 2026-11-22 carry no schema_version; normalise_row() adds 1",
    2: "rows carry schema_version=2 explicitly; no field was removed from v1",
}


def normalise_row(row: Mapping) -> dict:
    """Return a v2-shaped copy. A missing schema_version means v1, not corrupt."""
    out = dict(row)
    out["schema_version"] = int(out.get("schema_version") or 1)
    return out


def iter_rows(path: str | Path) -> Iterator[dict]:
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            yield normalise_row(json.loads(line))
        except ValueError:
            continue


def read_rows(path: str | Path) -> list[dict]:
    return list(iter_rows(path))


def validate_row(row: Mapping) -> list[str]:
    problems = [f"missing field: {key}" for key in REQUIRED_FIELDS if key not in row]
    version = int(row.get("schema_version") or 1)
    if version > SCHEMA_VERSION:
        problems.append(f"schema_version {version} is newer than this reader ({SCHEMA_VERSION})")
    return problems


def rows_for(rows: Iterable[Mapping], *, run_id: str | None = None,
             workflow: str | None = None, unit: str | None = None) -> list[dict]:
    out = []
    for row in rows:
        if run_id is not None and row.get("run_id") != run_id:
            continue
        if workflow is not None and row.get("workflow") != workflow:
            continue
        if unit is not None and row.get("item") != unit:
            continue
        out.append(normalise_row(row))
    return out


__all__ = [
    "ChainReport",
    "EvidenceCheck",
    "Gate",
    "GateRefused",
    "MIGRATION_NOTES",
    "REQUIRED_FIELDS",
    "SCHEMA_VERSION",
    "Stamp",
    "iter_rows",
    "normalise_row",
    "read_rows",
    "require",
    "rows_for",
    "sha256_bytes",
    "sha256_file",
    "validate_row",
    "verify_evidence_chain",
]

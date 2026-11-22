#!/usr/bin/env python3
"""E35 import half — agent-harness's binding to the shared gate library.

This module is deliberately additive: it imports `harness_shared` and
re-exports the evidence hash, run-record schema and one-way-door gate so
agent-harness code and workflow-harness code cannot drift into two copies.
It changes no existing gate behaviour; callers adopt the imports as they touch
each gate.

The package resolves as a sibling checkout (`<repo>/../harness-shared`) or an
installed `harness_shared`.
"""
from __future__ import annotations

import sys
from pathlib import Path

SHARED_ROOT = Path(__file__).resolve().parents[2] / "harness-shared"
if SHARED_ROOT.is_dir() and str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

import harness_shared  # noqa: E402
from harness_shared.evidence import sha256_bytes, sha256_file, verify_evidence_chain  # noqa: E402
from harness_shared.gates import Gate, GateRefused, Stamp, require  # noqa: E402
from harness_shared.run_record import (  # noqa: E402
    MIGRATION_NOTES,
    SCHEMA_VERSION,
    normalise_row,
    validate_row,
)

__all__ = [
    "Gate",
    "GateRefused",
    "MIGRATION_NOTES",
    "SCHEMA_VERSION",
    "Stamp",
    "harness_shared",
    "normalise_row",
    "require",
    "sha256_bytes",
    "sha256_file",
    "validate_row",
    "verify_evidence_chain",
]

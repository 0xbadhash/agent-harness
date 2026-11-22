"""Property-based tests for the gate parsers (E08).

Hypothesis is a dev dependency; when it is not installed this module skips so
the deterministic offline suite still runs. CI installs it from
requirements-dev.txt and exercises every property.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_pr_body  # noqa: E402
import check_red_green_cmds as red_green  # noqa: E402
import check_spec_grill  # noqa: E402
import gate_conventions  # noqa: E402


@settings(max_examples=100, derandomize=True)
@given(st.text(max_size=300))
def test_spec_path_is_stripped_and_marker_bound(text: str) -> None:
    path = gate_conventions.spec_path(text)
    assert path is None or (path and path == path.strip())
    if "**Spec:**" not in text:
        assert path is None


@settings(max_examples=100, derandomize=True)
@given(st.text(max_size=300))
def test_waiver_type_only_returns_known_values(text: str) -> None:
    kind = gate_conventions.waiver_type(text)
    assert kind is None or kind in gate_conventions.WAIVERS


@settings(max_examples=100, derandomize=True)
@given(st.text(max_size=400), st.text(max_size=40))
def test_grill_without_header_never_passes(body: str, label: str) -> None:
    if re.search(r"^##\s+Grill-me", body, re.IGNORECASE | re.MULTILINE):
        return
    ok, _ = check_spec_grill.check_spec_text(body, label=label or "spec")
    assert ok is False


@settings(max_examples=100, derandomize=True)
@given(st.text(max_size=300))
def test_red_green_extraction_never_invents_commands(text: str) -> None:
    red = red_green._extract(red_green.RED_RE, text)
    green = red_green._extract(red_green.GREEN_RE, text)
    assert red is None or red == red.strip().strip("`").strip()
    assert green is None or green == green.strip().strip("`").strip()


@settings(max_examples=100, derandomize=True)
@given(st.text(max_size=300))
def test_pr_body_section_never_crosses_next_heading(text: str) -> None:
    section = check_pr_body._section(text, "Smallest")
    if "## Smallest" not in text:
        assert section == ""
    assert "\n## " not in section


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

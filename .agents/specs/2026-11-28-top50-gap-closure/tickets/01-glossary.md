# 01 — Glossary artifact and gate

**What to build:** a real glossary file that the domain-term, collision, and compact-safety checks read, plus a standalone checker registered in hard gates.

**Kind:** feature
**Prefactor:** none
**Touches:** docs/glossary.md, scripts/check_glossary.py, scripts/spec_gate.py, scripts/check_compact_safety.py, scripts/hard_gates.py
**Blocked by:** None — can start immediately
**Status:** done

- [x] `docs/glossary.md` lists term, definition, and owner for every domain term used by the harness.
- [x] `scripts/check_glossary.py --root .` exits 0 on the file and 1 on a duplicate normalized term.
- [x] `spec_gate` and `check_compact_safety` accept `docs/glossary.md`.
- [x] `hard_gates` reports the glossary gate and skips when no file exists.

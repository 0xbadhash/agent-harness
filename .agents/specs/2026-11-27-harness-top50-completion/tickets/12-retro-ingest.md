# 12 — Retro transcript and PR-comment ingest

**What to build:** Retro reads local agent transcripts and PR review comments,
redacts secrets, and stores the evidence.

**Kind:** feature
**Prefactor:** none
**Blocked by:** None
**Estimate:** 190
**Status:** ready-for-agent

- [ ] `retro_job.py --transcripts` uses `agent_transcript.py` and drops secret-like
      lines before writing evidence
- [ ] `retro_job.py --pr-comments` accepts a local fixture and, with `--gh`,
      reads PR review threads
- [ ] Missing sources produce a note, not a crash
- [ ] `pytest tests/test_retro_ingest.py -q` covers redaction and offline paths

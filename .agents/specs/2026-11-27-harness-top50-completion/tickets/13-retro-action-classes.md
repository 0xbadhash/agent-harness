# 13 — Retro action classes

**What to build:** Every retro finding is classified into one of five action
classes that determine where it goes.

**Kind:** feature
**Prefactor:** none
**Blocked by:** 12
**Estimate:** 110
**Status:** ready-for-agent

- [ ] `retrospect` defines fix-now, add-gate, add-test, doc, and non-action
- [ ] `retro_job.py` emits the class per cluster and refuses an unknown class
- [ ] `pytest tests/test_retro_ingest.py -q` covers all five and the rejection

# 04 — Background merge stack

**What to build:** a detached merge mode with a log path and pid, leaving the default foreground behavior unchanged.

**Kind:** feature
**Prefactor:** none
**Touches:** scripts/merge_stack.py
**Blocked by:** None — can start immediately
**Status:** done

- [x] `--background` re-execs without the flag, detaches, writes the log, and prints pid and log.
- [x] A unit test covers the argv builder without spawning a process.
- [x] `--dry-run` output is unchanged.

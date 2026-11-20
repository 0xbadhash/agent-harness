# ENABLE RUNBOOK — busy parallel hook — t2064u

NEEDS A SEPARATE CEO STAMP — touches the gateway.

This worktree is staged and OFF. Nothing in `/home/debian/hermes` is registered.

## What changes at enable time

1. Copy `busy_parallel/` to `/home/debian/hermes/profiles/chief-of-staff/plugins/busy-parallel/` (package plus `plugin.py` `register`).
2. Add `busy-parallel` to that profile's `plugins.enabled` list.
3. Write `/home/debian/hermes/profiles/chief-of-staff/busy-parallel.yaml` with `allow_chats` set from the existing Signal `home_channel` CEO DM entry. Do not invent a second id. Do not commit that file.
4. Leave `state/busy-parallel/ENABLE` absent until the smoke below passes in dry-run.
5. Do not create `DISABLED` unless you want the hook to stay a no-op even after `ENABLE`.

A shell `hooks:` entry is not enough. `post_gateway_admission` shell stdout cannot return `{"action":"handled"}` (`agent/shell_hooks.py` parses that event as context only), so the chief would still run the same message later.

## Restart

Yes. A new plugin is loaded by `PluginManager.discover_and_load` at gateway start (`hermes_cli/plugins.py`). The ~30s watcher only re-syncs shell hooks (`gateway/run_profile_reconcile.py`). Restart `hermes-gateway-7e5c0db0.service` once, after the plugin files are in place and before creating `ENABLE`.

Confirm the process uses the session-authority path. The in-process busy fast-path (`gateway/run_inbound.py` `_hm_handle_running_session_message`) never calls this hook. Queue mode on the authority path does (`_hm_busy_preempt` returns false, then `post_gateway_admission`).

## Smoke

1. `BUSY_PARALLEL_MODE` unset (dry). Create `ENABLE`. Send nothing yet.
2. Feed a fixture JSON through `python -m busy_parallel.runner` with `HERMES_HOME` pointed at a copy, sender set to the CEO DM id. Expect `launch: true`, a kick file, `launched: false`.
3. Remove `ENABLE`. Repeat. Expect `switch-off`.
4. Only with the CEO stamp: set `BUSY_PARALLEL_MODE=live` in the gateway environment, restart, create `ENABLE`, and send one harmless CEO DM sentence while a turn is in flight ("busy parallel smoke, reply OK"). The worker job id starts `busy-par-`. The reply arrives on the CEO DM from the chief-of-staff profile. The chief's own later turn must not repeat it (`handled`).

## How the CEO knows

The DM gets one reply from the parallel worker while the original task keeps running. `journalctl --user -u hermes-gateway-7e5c0db0.service` shows `busy-parallel live allowlist-accept busy-par-` and no second signal-cli process.

## Rollback

Remove the plugin dir and the `plugins.enabled` line. Delete `state/busy-parallel/ENABLE` (or write `DISABLED`). Restart the gateway once so the plugin unloads. In-flight `hermes-kick.sh` children exit on their own; do not kill the gateway to stop them. Staged tree only: `git worktree remove /home/debian/busy-parallel-t2064u` and `git -C /home/debian/agent-harness branch -D feat/busy-parallel-t2064u`.

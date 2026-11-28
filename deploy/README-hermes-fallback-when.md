# Hermes fallback `when:` gate

CEO policy: the chief-of-staff lane may use DeepSeek only when Venice credits are
exhausted. Hermes' stock chain switches for billing, rate limits, upstream rate
limits and most other failures, so the policy needs a per-entry gate.

## What the patch changes

`deploy/patches/hermes-fallback-when.patch` (against the pinned Hermes checkout at
`/home/debian/hermes/hermes-agent`) adds one optional key to a
`fallback_providers` entry:

```yaml
fallback_providers:
  - provider: venice
    model: deepseek-v4-1-flash-uncensored
    when: [billing]
```

- `when` is a list of `FailoverReason` values the entry may serve. Absent or
  empty means every reason (stock behavior).
- `agent/chat_completion_helpers.py` gains `_fallback_entry_allows_reason()` and a
  gate in `try_activate_fallback()`. A gated entry is skipped for other reasons
  and stays in place (the chain index is restored), so a later billing failure in
  the same turn can still use it.
- The provider id is matched case-insensitively against `reason.value`; a missing
  reason never matches a non-empty gate.
- `tests/agent/test_fallback_when_gate.py` covers billing-only, other reasons,
  missing reason, ungated entries, and skip-forward to a later allowed entry.

`when:` is used instead of `on:` because PyYAML parses an unquoted `on` key as a
boolean.

`hermes fallback list` does not print `when` (its table predates the key), so read
the profile config to confirm the gate.

## Reapply after `hermes update`

The update autostashes local edits and restores them, but a conflict or a
discarded autostash loses the patch. Check, then reapply:

```sh
cd /home/debian/hermes/hermes-agent
git apply --check --reverse /home/debian/agent-harness/deploy/patches/hermes-fallback-when.patch \
  || git apply /home/debian/agent-harness/deploy/patches/hermes-fallback-when.patch
systemctl --user restart hermes-gateway-7e5c0db0.service
```

The config line lives in `profiles/chief-of-staff/config.yaml`; the updater does
not touch profile configs.

## Test

The Hermes venv has no pytest. Run from the checkout with the system pytest:

```sh
cd /home/debian/hermes/hermes-agent
PYTHONPATH=$PWD python3 -m pytest tests/agent/test_fallback_when_gate.py -q
```

`tests/agent/test_fallback_exhaustion_cooldown.py::TestRateLimitBackoffEscalation::test_backoff_counter_resets_on_successful_primary_restore`
fails under the system Python before and after this patch (`typing_extensions`
too old for `Sentinel`); it is an environment mismatch, not a regression.

## Rollback

```sh
cd /home/debian/hermes/hermes-agent
git apply --reverse /home/debian/agent-harness/deploy/patches/hermes-fallback-when.patch
# drop the `when: [billing]` line from the profile's fallback_providers entry
systemctl --user restart hermes-gateway-7e5c0db0.service
```

The restart is required either way: the gateway imports the module at process
start and agents reuse the loaded code.

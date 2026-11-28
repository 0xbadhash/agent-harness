#!/usr/bin/env bash
# Grok Notification hook -> auto-review relay.
#
# Silent by design: stdout and stderr are discarded so hook output never reaches
# the model's context, and every failure exits 0 so the hook can never block a
# turn. The relay does the filtering, redaction and rate limiting.
set -uo pipefail

RELAY="${AUTO_REVIEW_RELAY:-/opt/catalyxt/ops/auto-review-relay.py}"
PYTHON="${AUTO_REVIEW_PYTHON:-python3}"
TIMEOUT="${AUTO_REVIEW_TIMEOUT:-8}"
HARNESS="${AUTO_REVIEW_HARNESS:-grok}"

[ -r "$RELAY" ] || exit 0

payload="$(cat)"

args=(--hook --harness "$HARNESS")
if [ -n "${AUTO_REVIEW_DRY:-}" ]; then
  args+=(--dry)
fi

if command -v timeout >/dev/null 2>&1; then
  printf '%s' "$payload" | timeout -s TERM "$TIMEOUT" "$PYTHON" "$RELAY" "${args[@]}" >/dev/null 2>&1 || true
else
  printf '%s' "$payload" | "$PYTHON" "$RELAY" "${args[@]}" >/dev/null 2>&1 || true
fi

exit 0

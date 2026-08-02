#!/usr/bin/env bash
# Install morning-triage systemd units (opt-in). Default: dry-run.
set -euo pipefail
HARNESS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APPLY=0
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --dry-run) APPLY=0; shift ;;
    --systemd-dir) SYSTEMD_DIR="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--dry-run|--apply]"; exit 0 ;;
    *) echo "Unknown: $1" >&2; exit 2 ;;
  esac
done
SVC="$HARNESS_ROOT/deploy/morning-triage.service"
TMR="$HARNESS_ROOT/deploy/morning-triage.timer"
echo "install_morning_triage apply=$APPLY"
echo "  $SVC → $SYSTEMD_DIR/morning-triage.service"
echo "  $TMR → $SYSTEMD_DIR/morning-triage.timer"
if [[ "$APPLY" -eq 0 ]]; then
  echo "✅ dry-run (no changes). Use --apply with sudo when ready."
  exit 0
fi
cp -v "$SVC" "$SYSTEMD_DIR/morning-triage.service"
cp -v "$TMR" "$SYSTEMD_DIR/morning-triage.timer"
systemctl daemon-reload
systemctl enable --now morning-triage.timer
echo "✅ morning-triage.timer enabled"

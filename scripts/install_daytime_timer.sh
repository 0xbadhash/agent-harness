#!/usr/bin/env bash
# A3 — install daytime-gates systemd units (opt-in).
# Default: dry-run (print actions). Use --apply to copy + enable.
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APPLY=0
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"

usage() {
  cat <<EOF
Usage: $0 [--dry-run|--apply] [--systemd-dir DIR]

  --dry-run   Print planned actions (default)
  --apply     Copy deploy/daytime-gates.{service,timer} and systemctl enable --now timer
  --systemd-dir  Target unit dir (default: /etc/systemd/system)

Never runs enable without --apply.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --dry-run) APPLY=0; shift ;;
    --systemd-dir) SYSTEMD_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

SVC="$HARNESS_ROOT/deploy/daytime-gates.service"
TMR="$HARNESS_ROOT/deploy/daytime-gates.timer"
for f in "$SVC" "$TMR"; do
  if [[ ! -f "$f" ]]; then
    echo "❌ missing $f" >&2
    exit 1
  fi
done

echo "install_daytime_timer apply=$APPLY harness=$HARNESS_ROOT systemd_dir=$SYSTEMD_DIR"
echo "  would install: $SVC → $SYSTEMD_DIR/daytime-gates.service"
echo "  would install: $TMR → $SYSTEMD_DIR/daytime-gates.timer"
echo "  would: systemctl daemon-reload"
echo "  would: systemctl enable --now daytime-gates.timer"

if [[ "$APPLY" -eq 0 ]]; then
  echo "✅ dry-run complete (no changes). Re-run with --apply as root/sudo when ready."
  exit 0
fi

if [[ ! -w "$SYSTEMD_DIR" ]]; then
  echo "❌ $SYSTEMD_DIR not writable — re-run with sudo $0 --apply" >&2
  exit 1
fi

cp -v "$SVC" "$SYSTEMD_DIR/daytime-gates.service"
cp -v "$TMR" "$SYSTEMD_DIR/daytime-gates.timer"
systemctl daemon-reload
systemctl enable --now daytime-gates.timer
systemctl status daytime-gates.timer --no-pager || true
echo "✅ daytime-gates.timer enabled"

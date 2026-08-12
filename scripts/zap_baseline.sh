#!/usr/bin/env bash
# J13 — OWASP ZAP baseline against config/zap_targets.yaml (Docker).
# Default: warn-only (exit 0). Set ZAP_FAIL_CLOSED=1 or fail_closed: true for fail.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="${ZAP_TARGETS_FILE:-$ROOT/config/zap_targets.yaml}"
FAIL_CLOSED="${ZAP_FAIL_CLOSED:-}"
REPORT_DIR="${ZAP_REPORT_DIR:-$ROOT/.agents/artifacts/zap}"
mkdir -p "$REPORT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "⚠️  docker not available — ZAP baseline skipped"
  exit 0
fi

if [[ ! -f "$CFG" ]]; then
  echo "⚠️  no $CFG — skip"
  exit 0
fi

# Minimal YAML parse: lines with url: and enabled
mapfile -t URLS < <(python3 - <<'PY' "$CFG"
import sys
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
fail = "false"
urls = []
enabled = True
cur_url = None
for line in text.splitlines():
    s = line.strip()
    if s.startswith("fail_closed:"):
        fail = s.split(":", 1)[1].strip().lower()
    if s.startswith("- id:"):
        enabled = True
        cur_url = None
    if s.startswith("enabled:"):
        enabled = s.split(":", 1)[1].strip().lower() in ("true", "yes", "1")
    if s.startswith("url:"):
        cur_url = s.split(":", 1)[1].strip()
        if enabled and cur_url:
            urls.append(cur_url)
print(fail)
for u in urls:
    print(u)
PY
)

FAIL_FLAG="${URLS[0]:-false}"
if [[ -n "$FAIL_CLOSED" ]]; then
  FAIL_FLAG=$(echo "$FAIL_CLOSED" | tr '[:upper:]' '[:lower:]')
  [[ "$FAIL_FLAG" == "1" ]] && FAIL_FLAG=true
fi

rc=0
for url in "${URLS[@]:1}"; do
  [[ -z "$url" ]] && continue
  safe=$(echo "$url" | sed 's/[^a-zA-Z0-9]/_/g')
  echo "── ZAP baseline: $url"
  if docker run --rm -v "$REPORT_DIR:/zap/wrk:rw" -t ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py -t "$url" -r "zap-${safe}.html" -I 2>&1 | tee "$REPORT_DIR/zap-${safe}.log"; then
    echo "✅ ZAP finished (warnings allowed by -I): $url"
  else
    echo "❌ ZAP baseline issues: $url"
    if [[ "$FAIL_FLAG" == "true" ]]; then
      rc=1
    else
      echo "⚠️  warn-only (fail_closed=false)"
    fi
  fi
done

exit "$rc"


#!/usr/bin/env bash
set -euo pipefail
OUT=${1:-/var/backups/solbot/export-$(date +%Y%m%d-%H%M%S).ndjson}
mkdir -p "$(dirname "$OUT")"
redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" LRANGE solbot:reconcile 0 -1 | sed 's/^/{"reconcile":/;s/$/}/' > "$OUT"
echo "[export] wrote $OUT"

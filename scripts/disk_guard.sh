#!/usr/bin/env bash
set -euo pipefail
LOGDIR="${1:-logs}"
MAXSIZE=$((100*1024*1024)) # 100MB
# rotate large files
mkdir -p "$LOGDIR/old" || true
for f in "$LOGDIR"/*; do
  [ -f "$f" ] || continue
  sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  if [ "$sz" -gt "$MAXSIZE" ]; then
    ts=$(date +%Y%m%d%H%M%S)
    mv "$f" "$LOGDIR/old/$(basename "$f").$ts"
    gzip -f "$LOGDIR/old/$(basename "$f").$ts" || true
  fi
done
# purge old gz > 14 days
find "$LOGDIR/old" -type f -name "*.gz" -mtime +14 -delete 2>/dev/null || true
# disk usage alert
USE=$(df -h / | awk 'NR==2{gsub(/%/,"",$5); print $5}')
if [ "${USE:-0}" -ge 90 ]; then
  ./scripts/tg_notify.sh "⚠️ Disk usage ${USE}% on $(hostname) — purging old logs" >/dev/null 2>&1 || true
  find "$LOGDIR/old" -type f -mtime +3 -delete 2>/dev/null || true
fi

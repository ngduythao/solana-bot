#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
LOG_DIR="$ROOT/logs"
MAX_MIN="${IDLE_MAX_MIN:-15}"
NOW=$(date +%s)
latest=0
if [ -d "$LOG_DIR" ]; then
  for f in "$LOG_DIR"/*; do
    [ -f "$f" ] || continue
    ts=$(stat -c %Y "$f" 2>/dev/null || echo 0)
    if [ "$ts" -gt "$latest" ]; then latest="$ts"; fi
  done
fi
age=$(( (NOW - latest) / 60 ))
if [ "$age" -ge "$MAX_MIN" ]; then
  ./scripts/tg_notify.sh "♻️ Auto-restart: no fills/log update for ${age}min (threshold ${MAX_MIN}min)."
  ./scripts/engine_ctl.sh restart || true
fi

# Optional Redis-based last fill TS (key: hsbot:last_fill_ts)
R_TS=$(redis-cli GET hsbot:last_fill_ts 2>/dev/null || echo "")
if [ -n "$R_TS" ] && [[ "$R_TS" =~ ^[0-9]+$ ]]; then
  age=$(( (NOW - R_TS) / 60 ))
fi

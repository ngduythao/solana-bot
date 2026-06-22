#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="${AUTO_CONVERT_MODE:-off}"     # off | daily | always
HOUR="${AUTO_CONVERT_HOUR:-7}"       # local VN hour (0-23)
LOG="/var/log/solbot_convert.log"
STAMP="/opt/solbot/state/convert_daily.stamp"
mkdir -p /opt/solbot/state || true

log(){ echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

case "$MODE" in
  off)
    log "auto-convert: off"
    exit 0
    ;;
  daily)
    # Use Vietnam TZ for hour check
    TZ="Asia/Ho_Chi_Minh" export TZ
    NOW_H=$(date +%H)
    TODAY=$(date +%F)
    LAST="$(cat "$STAMP" 2>/dev/null || true)"
    if [ "$NOW_H" = "$HOUR" ] && [ "$LAST" != "$TODAY" ]; then
      log "auto-convert: daily trigger at $NOW_H VN; running convert_to_base.sh"
      ./scripts/convert_to_base.sh && log "auto-convert: completed" || log "auto-convert: convert failed"
      echo "$TODAY" > "$STAMP"
    else
      log "auto-convert: daily not due (now=$NOW_H, want=$HOUR, last=$LAST)"
    fi
    ;;
  always)
    # Best-effort periodic convert: run every 10 minutes max
    STAMP_AL="/opt/solbot/state/convert_always.stamp"
    NOW_S=$(date +%s); LAST_AL=$(cat "$STAMP_AL" 2>/dev/null || echo 0)
    if [ $((NOW_S - LAST_AL)) -ge 600 ]; then
      log "auto-convert: always trigger (>=10min); running convert_to_base.sh"
      ./scripts/convert_to_base.sh && log "auto-convert: completed" || log "auto-convert: convert failed"
      echo "$NOW_S" > "$STAMP_AL"
    else
      log "auto-convert: always skipped (cooldown)"
    fi
    ;;
  *)
    log "auto-convert: unknown mode '$MODE'"
    exit 1
    ;;
esac

# daily stop-loss check
if [ -f .env ]; then
  LOSS=$(redis-cli get hsbot:pnl:daily_loss 2>/dev/null)
  STOP=$(grep DAILY_STOP_LOSS_PCT .env | cut -d= -f2)
  if [ ! -z "$LOSS" ] && [ ! -z "$STOP" ]; then
    if [ $(echo "$LOSS < -$STOP" | bc) -eq 1 ]; then
      echo "[STOP-LOSS] Daily loss $LOSS < -$STOP%, pausing bot" >> /var/log/solbot_convert.log
      tg "⚠️ Stop-loss $STOP% triggered → bot paused."
      redis-cli set hsbot:paused 1 >/dev/null 2>&1 || true
      ./scripts/stop.sh || true
    fi
  fi
fi

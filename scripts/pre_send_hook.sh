#!/usr/bin/env bash
# Generic pre-send hook to call anti_pvp_guard; exit 1 to skip send
set -euo pipefail
PAIR="${PAIR:-${1:-}}"
SLOT="${SLOT:-${2:-0}}"
TIP="${TIP:-${3:-0}}"
MEDIAN="${WINDOW_MEDIAN_TIP:-${4:-0}}"
CROWD="${SLOT_PAIR_COUNT:-${5:-0}}"
export PAIR SLOT TIP WINDOW_MEDIAN_TIP MEDIAN SLOT_PAIR_COUNT CROWD
if ./scripts/anti_pvp_guard.py; then
  exit 0
else
  echo "[anti-pvp] skip pair=$PAIR slot=$SLOT tip=$TIP median=$MEDIAN crowd=$CROWD" >> logs/anti_pvp.log
  ./scripts/tg_notify.sh "⚠️ Anti-PvP skip on $PAIR at slot $SLOT (tip=$TIP, median=$MEDIAN, crowd=$CROWD)" >/dev/null 2>&1 || true
  exit 1
fi

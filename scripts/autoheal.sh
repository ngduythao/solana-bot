#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
while true; do
  missing=0
  for s in solbot_panel solbot_ws solbot_jito solbot_backrun solbot_risk solbot_pnlagg solbot_daily solbot_guard; do
    if ! tmux has-session -t "$s" 2>/dev/null; then
      echo "[autoheal] missing $s"
      missing=1
    fi
  done
  if [ "$missing" -eq 1 ]; then
    echo "[autoheal] re-running autorun"
    bash ./autorun_solbot.sh || true
  fi
  sleep 30
done

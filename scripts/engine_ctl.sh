#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cmd="${1:-}"
case "$cmd" in
  restart)
    "$0" stop || true
    "$0" start || true
    echo "[engine] restarted";
    ;;

  start)
    tmux kill-session -t solbot_backrun 2>/dev/null || true
    tmux kill-session -t solbot_jito 2>/dev/null || true
    tmux kill-session -t solbot_ws 2>/dev/null || true
    ./scripts/start.sh auto || true
    echo "[engine] started"
    ;;
  stop)
    ./scripts/stop.sh || true
    echo "[engine] stopped"
    ;;
  *)
    echo "usage: $0 <start|stop>"
    exit 1
    ;;
esac

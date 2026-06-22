
#!/usr/bin/env bash
# Blue/Green orchestrator — run green on alternative ports; swap traffic if healthy.
set -euo pipefail
MODE="${1:-status}"  # up|swap|down|status
GREEN_PORT="${GREEN_PORT:-8082}"
HEALTH="${HEALTH:-http://127.0.0.1:9090/ready}"

case "$MODE" in
  up)
    echo "[BG] starting green stack (detached via tmux)"
    tmux new -d -s solbot_green "cd $(pwd) && bash solana-bot/deploy/RUN_ME.sh"
    ;;
  swap)
    echo "[BG] checking health..."
    curl -sf "$HEALTH" >/dev/null && echo "[BG] healthy; swapping routes" || { echo "[BG] not healthy"; exit 1; }
    # Here we would swap nginx/haproxy routes; placeholder:
    echo "[BG] (placeholder) swap to green"
    ;;
  down)
    tmux kill-session -t solbot_green || true
    echo "[BG] green down"
    ;;
  status)
    tmux has-session -t solbot_green >/dev/null 2>&1 && echo "[BG] green RUNNING" || echo "[BG] green STOPPED"
    ;;
esac

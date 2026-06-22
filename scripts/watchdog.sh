#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
# Simple watchdog: restarts systemd or tmux sessions if dead
CHECKS=("solbot-prober" "solbot-jito-autotune" "solbot-scorer" "solbot-hedger" "solbot-hedge-policy")
for svc in "${CHECKS[@]}"; do
  if systemctl is-active --quiet "$svc"; then
    continue
  else
    echo "[!] $svc is not active, attempting start..."
    systemctl start "$svc" || true
  fi
done
# Fallback: ensure tmux sessions
which tmux >/dev/null 2>&1 || exit 0
for s in "${CHECKS[@]}"; do
  tmux has-session -t "$s" 2>/dev/null || true
done

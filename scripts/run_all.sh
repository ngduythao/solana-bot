#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate || true
export $(grep -v '^#' .env | xargs -d '\n' -I {} echo {} | xargs) || true

start_session () {
  local name="$1"; shift
  local cmd="$*"
  if tmux has-session -t "$name" 2>/dev/null; then
    echo "[=] $name already running"
  else
    tmux new-session -d -s "$name" "$cmd"
    echo "[+] Launched $name"
  fi
}

if [ -f backrun/backrun.py ]; then
  start_session solbot_backrun "cd $ROOT_DIR/backrun && source ../.venv/bin/activate && python3 backrun.py"
fi
if [ -f rpc_router/ws_listener.py ]; then
  start_session solbot_ws "cd $ROOT_DIR/rpc_router && source ../.venv/bin/activate && python3 ws_listener.py"
fi
if [ -f jito_submitter/submitter.py ]; then
  start_session solbot_jito "cd $ROOT_DIR/jito_submitter && source ../.venv/bin/activate && python3 submitter.py"
fi
if [ -f alerts_runner/alerts.py ]; then
  start_session solbot_alerts "cd $ROOT_DIR/alerts_runner && source ../.venv/bin/activate && python3 alerts.py"
fi

echo "[+] Use 'tmux ls' to inspect sessions."


# Hedge policy dynamic cfg
if [ -f ../services/hedge_policy.py ]; then
  start_session solbot_hedge_policy "cd $ROOT_DIR/services && source ../.venv/bin/activate && python3 hedge_policy.py"
fi

# start route penalty service
tmux new-session -d -s solbot_route_penalty 'cd "$(dirname "$0")/.." && exec python3 -m analytics.route_penalty'

# start auto notional guard
if [ "${NOTIONAL_GUARD_ENABLE:-1}" = "1" ]; then
  tmux new-session -d -s solbot_notional_guard 'cd "$(dirname "$0")/.." && exec python3 -m analytics.auto_notional_guard'
fi

# start auto tip guard
if [ "${TIP_GUARD_ENABLE:-1}" = "1" ]; then
  tmux new-session -d -s solbot_tip_guard 'cd "$(dirname "$0")/.." && exec python3 -m analytics.auto_tip_guard'
fi

# jito rtt prober
tmux new-session -d -s solbot_jito_prober 'cd "$(dirname "$0")/.." && exec python3 -m services.jito_prober'
# simulator regression runner
if [ "${SIM_ENABLE:-1}" = "1" ]; then tmux new-session -d -s solbot_simreg 'cd "$(dirname "$0")/.." && exec python3 -m analytics.regression_runner'; fi
# kelly sizer agent
if [ "${KELLY_ENABLE:-1}" = "1" ]; then tmux new-session -d -s solbot_kelly 'cd "$(dirname "$0")/.." && exec python3 -m analytics.kelly_sizer'; fi
# telegram alerts
if [ -n "${TG_BOT_TOKEN-}" ] && [ -n "${TG_CHAT_ID-}" ]; then tmux new-session -d -s solbot_alerts 'cd "$(dirname "$0")/.." && exec python3 -m alerts.telegram_alert'; fi

# start panel
"$(dirname "$0")/serve_dashboard.sh" || true

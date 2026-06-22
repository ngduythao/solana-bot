#!/usr/bin/env bash
set -euo pipefail
declare -a SESS=(solbot_stopgain solbot_rebalance solbot_stoploss solbot_dailysum solbot_pnlw solbot_wserr solbot_wsrtr solbot_wswatch solbot_rpcrtr solbot_rpcwatch solbot_ws solbot_backrun solbot_jito solbot_panel solbot_metrics solbot_caps solbot_block solbot_pacer solbot_rhealth)
for s in "${SESS[@]}"; do
  if ! tmux has-session -t "$s" 2>/dev/null; then
    echo "[heal] restart $s"
    case "$s" in
      solbot_stopgain) tmux new-session -d -s solbot_stopgain "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; BASE_EQUITY_USD=${BASE_EQUITY_USD:-10000} STOPGAIN_DAILY_PCT=${STOPGAIN_DAILY_PCT:-10} python3 -u scripts/stopgain_watch.py >> logs/stopgain.log 2>&1" ;;
      solbot_rebalance) tmux new-session -d -s solbot_rebalance "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; REBALANCE_NONUSDC_THRESHOLD_PCT=${REBALANCE_NONUSDC_THRESHOLD_PCT:-5} python3 -u scripts/rebalance_daily.py >> logs/rebalance.log 2>&1" ;;

      solbot_stoploss) tmux new-session -d -s solbot_stoploss "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; BASE_EQUITY_USD=${BASE_EQUITY_USD:-10000} STOPLOSS_DAILY_PCT=${STOPLOSS_DAILY_PCT:-3} python3 -u scripts/stoploss_watch.py >> logs/stoploss.log 2>&1" ;;
      solbot_dailysum) tmux new-session -d -s solbot_dailysum "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/daily_summary.py >> logs/daily_summary.log 2>&1" ;;

      solbot_pnlw) tmux new-session -d -s solbot_pnlw "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/pnl_watch.py >> logs/pnl_watch.log 2>&1" ;;

      solbot_wserr) tmux new-session -d -s solbot_wserr "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/ws_error_watch.py >> logs/ws_error.log 2>&1" ;;

      solbot_wsrtr) tmux new-session -d -s solbot_wsrtr "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/ws_force_router.py >> logs/ws_router.log 2>&1" ;;
      solbot_wswatch) tmux new-session -d -s solbot_wswatch "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/ws_current_watch.py >> logs/ws_watch.log 2>&1" ;;

      solbot_ws)      ./scripts/run_ws.sh &;;
      solbot_backrun) ./scripts/run_backrun.sh &;;
      solbot_jito)    ./scripts/run_jito.sh &;;
      solbot_panel)   ./scripts/run_panel.sh &;;
      solbot_metrics) ./scripts/run_metrics.sh &;;
      solbot_caps)    ./scripts/run_caps.sh &;;
      solbot_block)   tmux new-session -d -s solbot_block "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/block_fullness_probe.py >> logs/block_probe.log 2>&1" ;;
      solbot_pacer)   tmux new-session -d -s solbot_pacer "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/pacing_daemon.py >> logs/pacing.log 2>&1" ;;
      solbot_rhealth) tmux new-session -d -s solbot_rhealth "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/relay_health_daemon.py >> logs/relay_health.log 2>&1" ;;
    esac
  fi
done

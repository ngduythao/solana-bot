#!/usr/bin/env bash
set -euo pipefail
./run.sh
docker compose up -d jito_manager fee_tuner inventory_manager alerter latency_meter   hedge_worker stats_aggregator latency_hook_demo capital_manager order_executor allocator ws_slot_stream watchdog metrics_panel rpc_autoswitch risk_windows alert_logger trim_worker route_pnl_agg route_prefetcher prom_exporter sizing_autothrottle
echo "All core + auxiliary services are up. Dashboard: http://localhost:8080"

# jito rtt prober
tmux new-session -d -s solbot_jito_prober 'cd "$(pwd)" && exec python3 -m services.jito_prober'
# simulator regression runner
if [ "${SIM_ENABLE:-1}" = "1" ]; then tmux new-session -d -s solbot_simreg 'cd "$(pwd)" && exec python3 -m analytics.regression_runner'; fi
# kelly sizer agent
if [ "${KELLY_ENABLE:-1}" = "1" ]; then tmux new-session -d -s solbot_kelly 'cd "$(pwd)" && exec python3 -m analytics.kelly_sizer'; fi
# telegram alerts
if [ -n "${TG_BOT_TOKEN-}" ] && [ -n "${TG_CHAT_ID-}" ]; then tmux new-session -d -s solbot_alerts 'cd "$(pwd)" && exec python3 -m alerts.telegram_alert'; fi

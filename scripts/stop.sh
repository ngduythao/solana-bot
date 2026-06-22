#!/usr/bin/env bash
set -euo pipefail
for s in solbot_failover solbot_notional_guard solbot_tip_guard solbot_route_penalty solbot_jito_prober solbot_simreg solbot_kelly solbot_alerts; do tmux kill-session -t "$s" 2>/dev/null || true; done

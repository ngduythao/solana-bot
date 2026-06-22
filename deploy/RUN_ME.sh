
#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
# locate project base
proj=$(python3 - <<'PY'
import os
root=os.getcwd()
for dp, dn, fn in os.walk(root):
    if dp.endswith("solana-bot") and all(os.path.exists(os.path.join(dp,f)) for f in ["requirements_min.txt","p0_launcher.py"]):
        print(dp); break
PY
)
cd "$proj"
echo "[RUN_ME] project: $proj"
python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_min.txt
[ -f .env ] || cp .env.example .env
echo "[RUN_ME] launching core + P0 + CU estimator + reconciler"
# run everything in tmux if available; else foreground with multiprocess launcher
if command -v tmux >/dev/null 2>&1; then
  tmux new-session -d -s solbot "python run_oneclick.py"
  tmux split-window -v "python p0_launcher.py"
  tmux split-window -v "python services/cu_estimator.py"
  tmux split-window -v "python services/fill_reconciler.py"
  tmux split-window -v "python services/notifier_advanced.py"; tmux split-window -v "python services/rpc_ws_service.py"; tmux split-window -v "python services/auto_hedge_router_v2.py"; tmux attach -t solbot
else
  python run_oneclick.py &
  python p0_launcher.py &
  python services/cu_estimator.py &
  python services/fill_reconciler.py &
  wait
fi


# Idempotent ensures
ensure () { p=$1; shift; if ! pgrep -f "$p" >/dev/null 2>&1; then echo "[RUN_ME] starting $p"; eval "$@ &"; fi }
ensure "boot_watchdog.py" "$VENV/bin/python services/boot_watchdog.py"
ensure "plan_executor.py" "$VENV/bin/python services/plan_executor.py"
ensure "jupiter_executor.py" "$VENV/bin/python services/jupiter_executor.py"
ensure "relay_tipcurve.py" "$VENV/bin/python services/relay_tipcurve.py"
ensure "relay_slo_agg.py" "$VENV/bin/python services/relay_slo_agg.py"
ensure "jito_land_latency.py" "$VENV/bin/python services/jito_land_latency.py"
ensure "bridge_executor.py" "$VENV/bin/python services/bridge_executor.py"

  python services/wormhole_bridge.py &
  python services/colo_rtt.py &
  python services/wormhole_bridge_executor.py &
  python services/circuit_breaker.py &
  python services/alerts_manager.py &
  python services/health_watchdog.py &
  python services/telegram_notifier.py &
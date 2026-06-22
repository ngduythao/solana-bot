
#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$BASE_DIR/solana-bot"
cd "$APP_DIR"
source .venv/bin/activate || { python3 -m venv .venv && source .venv/bin/activate; }
pip install --upgrade pip >/dev/null
REQ="requirements_min.txt"; [ -f requirements.txt ] && REQ="requirements.txt"
pip install -r "$REQ" >/dev/null
# Start services in background (simple nohup)
nohup python services/env_validator.py >/tmp/env_validator.log 2>&1 &
nohup python services/jito_client.py >/tmp/jito_client.log 2>&1 &
nohup python services/onchain_populator.py >/tmp/onchain_populator.log 2>&1 &
nohup python dashboard_pro.py >/tmp/dashboard_pro.log 2>&1 &
nohup python services/policy_optimizer.py >/tmp/policy_optimizer.log 2>&1 &
nohup python services/policy_autopilot_lite.py >/tmp/policy_autopilot_lite.log 2>&1 &
nohup python services/fee_policy.py >/tmp/fee_policy.log 2>&1 &
nohup python services/auto_hedge_router_v2.py >/tmp/auto_hedge_router_v2.log 2>&1 &
nohup python services/auto_hedge_router.py >/tmp/auto_hedge_router.log 2>&1 &
nohup python services/auto_hedge_exec.py >/tmp/auto_hedge_exec.log 2>&1 &
nohup python services/notifier.py >/tmp/notifier.log 2>&1 &
nohup python services/notifier_advanced.py >/tmp/notifier_advanced.log 2>&1 &
nohup python services/rpc_ws_service.py >/tmp/rpc_ws_service.log 2>&1 &
nohup python services/watchdog.py >/tmp/watchdog.log 2>&1 &
echo "[AUTORUN] Started. Logs in /tmp/*.log"
echo "Dashboards: http://$(hostname -I | awk '{print $1}'):8080  and  http://$(hostname -I | awk '{print $1}'):8081/pro"

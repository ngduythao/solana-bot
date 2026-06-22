
#!/usr/bin/env bash
# Ubuntu 24.04 one-click install as systemd services (Vultr / Linuxpatch compatible)
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
  echo "Run as root: sudo bash deploy/install_systemd.sh"
  exit 1
fi
BASE_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$BASE_DIR/solana-bot"

# Python env
apt-get update -y
apt-get install -y python3-venv python3-pip
python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_min.txt

# Create env if missing
[ -f .env ] || cp .env.example .env

cat >/etc/systemd/system/solbot_core.service <<EOF
[Unit]
Description=Solbot Core (preselector+backrun+dashboard)
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python run_oneclick.py
Restart=always
RestartSec=2
User=%I
EOF

cat >/etc/systemd/system/solbot_p0.service <<EOF
[Unit]
Description=Solbot P0 (jito_client + fee_policy)
After=solbot_core.service

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python p0_launcher.py
Restart=always
RestartSec=2
User=%I
EOF

cat >/etc/systemd/system/solbot_cu.service <<EOF
[Unit]
Description=Solbot CU Estimator
After=solbot_core.service

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/cu_estimator.py
Restart=always
RestartSec=2
User=%I
EOF

cat >/etc/systemd/system/solbot_reconciler.service <<EOF
[Unit]
Description=Solbot Fill Reconciler
After=solbot_core.service

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/fill_reconciler.py
Restart=always
RestartSec=2
User=%I
EOF

systemctl daemon-reload
# Use current user for services (override with: systemctl enable solbot_core@youruser)
login_user=$(logname || echo "root")
systemctl enable solbot_core@${login_user}
systemctl enable solbot_p0@${login_user}
systemctl enable solbot_cu@${login_user}
systemctl enable solbot_reconciler@${login_user}
systemctl start solbot_core@${login_user}
systemctl start solbot_p0@${login_user}
systemctl start solbot_cu@${login_user}
systemctl start solbot_reconciler@${login_user}

echo "Installed systemd units for user ${login_user}. Use: systemctl status solbot_core@${login_user}"


cat >/etc/systemd/system/solbot_rpcws.service <<EOF
[Unit]
Description=Solbot WebSocket RPC Service
After=network-online.target

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/rpc_ws_service.py
Restart=always
RestartSec=2
User=%I
EOF

cat >/etc/systemd/system/solbot_notifier_adv.service <<EOF
[Unit]
Description=Solbot Advanced Notifier
After=network-online.target

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/notifier_advanced.py
Restart=always
RestartSec=5
User=%I
EOF

cat >/etc/systemd/system/solbot_autohedge_v2.service <<EOF
[Unit]
Description=Solbot Auto Hedge Router v2
After=solbot_core.service

[Service]
# Hardening include
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/auto_hedge_router_v2.py
Restart=always
RestartSec=2
User=%I
EOF

systemctl enable solbot_rpcws@${login_user}
systemctl enable solbot_notifier_adv@${login_user}
systemctl enable solbot_autohedge_v2@${login_user}
systemctl start solbot_rpcws@${login_user}
systemctl start solbot_notifier_adv@${login_user}
systemctl start solbot_autohedge_v2@${login_user}


mkdir -p /etc/solbot
cp "$BASE_DIR/solana-bot/deploy/hardening.conf" /etc/solbot/hardening.conf


cat >/etc/systemd/system/solbot_webhook.service <<EOF
[Unit]
Description=Solbot solbot_webhook
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/backrun_webhook.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_webhook@${login_user}
systemctl start solbot_webhook@${login_user}


cat >/etc/systemd/system/solbot_presim.service <<EOF
[Unit]
Description=Solbot solbot_presim
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/pre_sim_hook.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_presim@${login_user}
systemctl start solbot_presim@${login_user}


cat >/etc/systemd/system/solbot_toxic.service <<EOF
[Unit]
Description=Solbot solbot_toxic
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/toxicity_policy.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_toxic@${login_user}
systemctl start solbot_toxic@${login_user}


cat >/etc/systemd/system/solbot_slo.service <<EOF
[Unit]
Description=Solbot solbot_slo
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/slo_monitor.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_slo@${login_user}
systemctl start solbot_slo@${login_user}


cat >/etc/systemd/system/solbot_antipvp.service <<EOF
[Unit]
Description=Solbot solbot_antipvp
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/anti_pvp_guard.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_antipvp@${login_user}
systemctl start solbot_antipvp@${login_user}


cat >/etc/systemd/system/solbot_presim_plus.service <<EOF
[Unit]
Description=Solbot solbot_presim_plus
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/pre_sim_hook_plus.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_presim_plus@${login_user}
systemctl start solbot_presim_plus@${login_user}


cat >/etc/systemd/system/solbot_canary.service <<EOF
[Unit]
Description=Solbot solbot_canary
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/canary_tx.py
User=%I
Restart=always
RestartSec=2
EOF

systemctl enable solbot_canary@${login_user}
systemctl start solbot_canary@${login_user}


cat >/etc/systemd/system/solbot_alerts.service <<EOF
[Unit]
Description=Solbot Telegram Alerts
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/telegram_alerts.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_alerts@${login_user}
systemctl start  solbot_alerts@${login_user}


cat >/etc/systemd/system/solbot_rpc_rotator.service <<EOF
[Unit]
Description=Solbot RPC Rotator
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/rpc_rotator.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_rpc_rotator@${login_user}
systemctl start  solbot_rpc_rotator@${login_user}


cat >/etc/systemd/system/solbot_anomaly.service <<EOF
[Unit]
Description=Solbot solbot_anomaly
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/anomaly_guard.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_anomaly@${login_user}
systemctl start  solbot_anomaly@${login_user}


cat >/etc/systemd/system/solbot_scheduler.service <<EOF
[Unit]
Description=Solbot solbot_scheduler
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/lane_scheduler.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_scheduler@${login_user}
systemctl start  solbot_scheduler@${login_user}


cat >/etc/systemd/system/solbot_cb.service <<EOF
[Unit]
Description=Solbot solbot_cb
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/circuit_breaker.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_cb@${login_user}
systemctl start  solbot_cb@${login_user}


cat >/etc/systemd/system/solbot_warm.service <<EOF
[Unit]
Description=Solbot solbot_warm
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/warm_cache.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_warm@${login_user}
systemctl start  solbot_warm@${login_user}


cat >/etc/systemd/system/solbot_chaos.service <<EOF
[Unit]
Description=Solbot solbot_chaos
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/chaos_tester.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_chaos@${login_user}
systemctl start  solbot_chaos@${login_user}


cat >/etc/systemd/system/solbot_ai_ev.service <<EOF
[Unit]
Description=Solbot solbot_ai_ev
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/ai_ev_model.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_ai_ev@${login_user}
systemctl start  solbot_ai_ev@${login_user}


cat >/etc/systemd/system/solbot_ab_lane.service <<EOF
[Unit]
Description=Solbot solbot_ab_lane
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/ab_lane_policy.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_ab_lane@${login_user}
systemctl start  solbot_ab_lane@${login_user}


cat >/etc/systemd/system/solbot_alloc.service <<EOF
[Unit]
Description=Solbot solbot_alloc
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/ev_allocator.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_alloc@${login_user}
systemctl start  solbot_alloc@${login_user}


cat >/etc/systemd/system/solbot_kill.service <<EOF
[Unit]
Description=Solbot solbot_kill
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/kill_switch.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_kill@${login_user}
systemctl start  solbot_kill@${login_user}


cat >/etc/systemd/system/solbot_throttle.service <<EOF
[Unit]
Description=Solbot solbot_throttle
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/self_throttle.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_throttle@${login_user}
systemctl start  solbot_throttle@${login_user}


cat >/etc/systemd/system/solbot_pair_whitelist.service <<EOF
[Unit]
Description=Solbot solbot_pair_whitelist
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/pair_whitelist.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_pair_whitelist@${login_user}
systemctl start  solbot_pair_whitelist@${login_user}


cat >/etc/systemd/system/solbot_stealth.service <<EOF
[Unit]
Description=Solbot solbot_stealth
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/stealth_strategy.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_stealth@${login_user}
systemctl start  solbot_stealth@${login_user}


cat >/etc/systemd/system/solbot_fast.service <<EOF
[Unit]
Description=Solbot FastPath Executor
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/fast_executor.py
Restart=always
RestartSec=1
User=%I
EOF

systemctl enable solbot_fast@${login_user}
systemctl start  solbot_fast@${login_user}


cat >/etc/systemd/system/solbot_cost.service <<EOF
[Unit]
Description=Solbot solbot_cost
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/cost_model.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_cost@${login_user}
systemctl start  solbot_cost@${login_user}


cat >/etc/systemd/system/solbot_feeopt.service <<EOF
[Unit]
Description=Solbot solbot_feeopt
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/fee_optimizer.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_feeopt@${login_user}
systemctl start  solbot_feeopt@${login_user}


cat >/etc/systemd/system/solbot_capplan.service <<EOF
[Unit]
Description=Solbot solbot_capplan
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/capital_planner.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_capplan@${login_user}
systemctl start  solbot_capplan@${login_user}


cat >/etc/systemd/system/solbot_rebal.service <<EOF
[Unit]
Description=Solbot solbot_rebal
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/region_rebalancer.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_rebal@${login_user}
systemctl start  solbot_rebal@${login_user}


cat >/etc/systemd/system/solbot_hedge.service <<EOF
[Unit]
Description=Solbot solbot_hedge
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/hedge_perp.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_hedge@${login_user}
systemctl start  solbot_hedge@${login_user}


cat >/etc/systemd/system/solbot_tipwatch.service <<EOF
[Unit]
Description=Solbot solbot_tipwatch
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/tipstream_watcher.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_tipwatch@${login_user}
systemctl start  solbot_tipwatch@${login_user}


cat >/etc/systemd/system/solbot_guard.service <<EOF
[Unit]
Description=Solbot solbot_guard
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/budget_guard.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_guard@${login_user}
systemctl start  solbot_guard@${login_user}


cat >/etc/systemd/system/solbot_rebalance.service <<EOF
[Unit]
Description=Solbot solbot_rebalance
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/rebalance_planner.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_rebalance@${login_user}
systemctl start  solbot_rebalance@${login_user}


cat >/etc/systemd/system/solbot_attrib.service <<EOF
[Unit]
Description=Solbot solbot_attrib
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/pnl_attrib.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_attrib@${login_user}
systemctl start  solbot_attrib@${login_user}


cat >/etc/systemd/system/solbot_rebalplan.service <<EOF
[Unit]
Description=Solbot solbot_rebalplan
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/rebalance_plan.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_rebalplan@${login_user}
systemctl start  solbot_rebalplan@${login_user}


cat >/etc/systemd/system/solbot_budget.service <<EOF
[Unit]
Description=Solbot solbot_budget
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/budget_guard.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_budget@${login_user}
systemctl start  solbot_budget@${login_user}


cat >/etc/systemd/system/solbot_pnlattr.service <<EOF
[Unit]
Description=Solbot solbot_pnlattr
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/pnl_attr.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_pnlattr@${login_user}
systemctl start  solbot_pnlattr@${login_user}


cat >/etc/systemd/system/solbot_seal.service <<EOF
[Unit]
Description=Solbot solbot_seal
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/runtime_seal.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_seal@${login_user}
systemctl start  solbot_seal@${login_user}


cat >/etc/systemd/system/solbot_antidbg.service <<EOF
[Unit]
Description=Solbot solbot_antidbg
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/anti_debug.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_antidbg@${login_user}
systemctl start  solbot_antidbg@${login_user}


cat >/etc/systemd/system/solbot_honeypot.service <<EOF
[Unit]
Description=Solbot solbot_honeypot
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/honeypot.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_honeypot@${login_user}
systemctl start  solbot_honeypot@${login_user}


cat >/etc/systemd/system/solbot_noise.service <<EOF
[Unit]
Description=Solbot Stealth Noise
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/stealth_noise.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_noise@${login_user}
systemctl start  solbot_noise@${login_user}


cat >/etc/systemd/system/solbot_gas.service <<EOF
[Unit]
Description=Solbot solbot_gas
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/gas_keeper.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_gas@${login_user}
systemctl start  solbot_gas@${login_user}


cat >/etc/systemd/system/solbot_treasplit.service <<EOF
[Unit]
Description=Solbot solbot_treasplit
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/treasury_split.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_treasplit@${login_user}
systemctl start  solbot_treasplit@${login_user}


cat >/etc/systemd/system/solbot_pnlsettle.service <<EOF
[Unit]
Description=Solbot solbot_pnlsettle
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/pnl_settlement.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_pnlsettle@${login_user}
systemctl start  solbot_pnlsettle@${login_user}


cat >/etc/systemd/system/solbot_treasury.service <<EOF
[Unit]
Description=Solbot solbot_treasury
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/treasury_split.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_treasury@${login_user}
systemctl start  solbot_treasury@${login_user}


cat >/etc/systemd/system/solbot_settle.service <<EOF
[Unit]
Description=Solbot solbot_settle
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/treasury_settle.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_settle@${login_user}
systemctl start  solbot_settle@${login_user}


cat >/etc/systemd/system/solbot_compound.service <<EOF
[Unit]
Description=Solbot solbot_compound
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/profit_compounder.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_compound@${login_user}
systemctl start  solbot_compound@${login_user}


cat >/etc/systemd/system/solbot_rollpnl.service <<EOF
[Unit]
Description=Solbot solbot_rollpnl
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/rolling_pnl.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_rollpnl@${login_user}
systemctl start  solbot_rollpnl@${login_user}


cat >/etc/systemd/system/solbot_boot.service <<EOF
[Unit]
Description=Solbot solbot_boot
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/boot_watchdog.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_boot@${login_user}
systemctl start  solbot_boot@${login_user}


cat >/etc/systemd/system/solbot_planexec.service <<EOF
[Unit]
Description=Solbot solbot_planexec
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/plan_executor.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_planexec@${login_user}
systemctl start  solbot_planexec@${login_user}


cat >/etc/systemd/system/solbot_jupiter.service <<EOF
[Unit]
Description=Solbot solbot_jupiter
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/jupiter_executor.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_jupiter@${login_user}
systemctl start  solbot_jupiter@${login_user}


cat >/etc/systemd/system/solbot_bridge.service <<EOF
[Unit]
Description=Solbot solbot_bridge
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/bridge_planner.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_bridge@${login_user}
systemctl start  solbot_bridge@${login_user}


cat >/etc/systemd/system/solbot_tipcurve.service <<EOF
[Unit]
Description=Solbot Relay Tip-Curve
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/relay_tipcurve.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_tipcurve@${login_user}
systemctl start  solbot_tipcurve@${login_user}


cat >/etc/systemd/system/solbot_sloagg.service <<EOF
[Unit]
Description=Solbot Relay SLO Aggregator
After=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/relay_slo_agg.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_sloagg@${login_user}
systemctl start  solbot_sloagg@${login_user}


cat >/etc/systemd/system/solbot_bridge_real.service <<EOF
[Unit]
Description=Solbot solbot_bridge_real
After=network-online.target
[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/bridge_real.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_bridge_real@${login_user}
systemctl start solbot_bridge_real@${login_user}


cat >/etc/systemd/system/solbot_landlat.service <<EOF
[Unit]
Description=Solbot solbot_landlat
After=network-online.target
[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/relay_landlat.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_landlat@${login_user}
systemctl start solbot_landlat@${login_user}


cat >/etc/systemd/system/solbot_jito_land.service <<EOF
[Unit]
Description=Solbot solbot_jito_land
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/jito_land_latency.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_jito_land@${login_user}
systemctl start  solbot_jito_land@${login_user}


cat >/etc/systemd/system/solbot_bridge_exec.service <<EOF
[Unit]
Description=Solbot solbot_bridge_exec
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/bridge_executor.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_bridge_exec@${login_user}
systemctl start  solbot_bridge_exec@${login_user}


cat >/etc/systemd/system/solbot_wormhole.service <<EOF
[Unit]
Description=Solbot solbot_wormhole
After=network-online.target redis-server.service

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/wormhole_bridge.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_wormhole@${login_user}
systemctl start solbot_wormhole@${login_user}


cat >/etc/systemd/system/solbot_colo_rtt.service <<EOF
[Unit]
Description=Solbot solbot_colo_rtt
After=network-online.target redis-server.service

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/colo_rtt.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_colo_rtt@${login_user}
systemctl start solbot_colo_rtt@${login_user}


cat >/etc/systemd/system/solbot_wormbridge.service <<EOF
[Unit]
Description=Solbot solbot_wormbridge
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/wormhole_bridge_executor.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_wormbridge@${login_user}
systemctl start  solbot_wormbridge@${login_user}


cat >/etc/systemd/system/solbot_circuit.service <<EOF
[Unit]
Description=Solbot solbot_circuit
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/circuit_breaker.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_circuit@${login_user}
systemctl start  solbot_circuit@${login_user}


cat >/etc/systemd/system/solbot_health.service <<EOF
[Unit]
Description=Solbot solbot_health
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/health_watchdog.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_health@${login_user}
systemctl start  solbot_health@${login_user}


cat >/etc/systemd/system/solbot_telegram.service <<EOF
[Unit]
Description=Solbot Telegram Notifier
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/telegram_notifier.py
Restart=always
RestartSec=5
User=%I
EOF

systemctl enable solbot_telegram@${login_user}
systemctl start  solbot_telegram@${login_user}

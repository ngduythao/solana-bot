#!/usr/bin/env bash
set -euo pipefail

# deps auto-install
PKGS=(python3 python3-venv python3-pip redis-server tmux curl jq gnupg unzip)
MISSING=()
for p in "${PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p"); done
if [ ${#MISSING[@]} -gt 0 ]; then
  echo "[*] Installing missing packages: ${MISSING[*]}"
  apt-get update -y && apt-get install -y "${MISSING[@]}" || true
fi

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DEBIAN_FRONTEND=noninteractive
apt update -y
apt install -y python3 python3-venv python3-pip redis-server tmux curl jq gnupg unzip ca-certificates ufw chrony
systemctl enable --now redis-server chrony || true
[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel >/dev/null 2>&1 || true
[ -f requirements.txt ] && pip install -r requirements.txt || true
[ -f analytics/requirements.txt ] && pip install -r analytics/requirements.txt || true
./scripts/stop.sh || true
./scripts/start.sh auto || true
./scripts/run_all.sh || true
echo "[OK] Autorun finished."
# ---------- panel boot verification & auto-repair ----------
PANEL_BOOT_CHECK=1
echo "[autorun] Checking panel health at 127.0.0.1:8080 ..."
ok=0
for i in $(seq 1 12); do
  if curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
    ok=1
    echo "[autorun] Panel is healthy."
    break
  fi
  echo "[autorun] Panel not ready (try $i). Attempting repair..."
  # try backend repair endpoint if API root is up
  curl -fsS -X POST http://127.0.0.1:8080/wizard/repair -d "service=panel" >/dev/null 2>&1 || true
  # fallback to start script
  bash -lc "chmod +x ./scripts/start.sh && ./scripts/start.sh panel" || true
  sleep 5
done

if [ "$ok" != "1" ]; then
  echo "[autorun] WARNING: panel still not listening after retries. Check logs/panel_autoheal.log and tmux sessions."
else
  echo "[autorun] Panel is up on 127.0.0.1:8080"
fi
# -----------------------------------------------------------
echo "Panel should be at: http://$(hostname -I | awk '{print $1}'):8080/"

"./scripts/serve_dashboard.sh" || true


# Install/enable panel systemd unit (localhost)
cp -f systemd_solbot_panel.service /etc/systemd/system/solbot-panel.service
systemctl daemon-reload
systemctl enable --now solbot-panel.service || true

# First-run watchdog (ensure healthy)
./scripts/panel_watchdog.sh || true


# Disable legacy units if present
systemctl disable --now solbot.service 2>/dev/null || true
systemctl disable --now solbot-panel.service 2>/dev/null || true

# Install unified systemd unit
cp -f systemd_solbot_all.service /etc/systemd/system/solbot-all.service
systemctl daemon-reload
systemctl enable --now solbot-all.service


# Install cron health-check (every minute) - idempotent
CRON_LINE="* * * * * /bin/bash -lc 'cd %h/solbot && ./scripts/cron_healthcheck.sh'"
# Replace %h with /root for root's home (common on Ubuntu cloud images)
CRON_LINE=${CRON_LINE//%h/\/root}
( crontab -l 2>/dev/null | grep -v 'scripts/cron_healthcheck.sh' ; echo "$CRON_LINE" ) | crontab -
echo "[cron] Installed: $CRON_LINE"

# Cron VN 7AM daily PnL (Asia/Ho_Chi_Minh ~ UTC+7) - runs at minute 0 hour 0 UTC -> 7AM VN by cron TZ
( crontab -l 2>/dev/null; echo '0 0 * * * TZ=Asia/Ho_Chi_Minh /bin/bash -lc "cd /root/solbot && ./.venv/bin/python3 analytics/telegram_daily_report.py"' ) | crontab -

# Cron RTT prober (every 2 minutes)
( crontab -l 2>/dev/null | grep -v rtt_prober.sh ; echo '*/2 * * * * /bin/bash -lc "cd /root/solbot && ./scripts/rtt_prober.sh"') | crontab -

# Ensure alerts default enabled
mkdir -p /opt/solbot/state && echo "1" > /opt/solbot/state/alerts_enabled || true

# Normalize CRLF and ensure exec
find scripts -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; -exec chmod +x {} \; 2>/dev/null || true

# One-time infra checks (best-effort)
mkdir -p /var/log
./scripts/fw_check.sh  > /var/log/solbot_fwcheck.log  2>&1 || true
./scripts/net_benchmark.sh > /var/log/solbot_netbench.log 2>&1 || true

# Cron idle guard (every 2 minutes, restart engine if idle too long)
( crontab -l 2>/dev/null | grep -v idle_guard.sh ; echo '*/2 * * * * /bin/bash -lc "cd /root/solbot && ./scripts/idle_guard.sh"' ) | crontab -

# Basic VPS hardening (best-effort, safe for Vultr Ubuntu 24.04 & linuxpatch)
./scripts/harden_vps.sh || true

# Preflight checks (best-effort, no hard fail)
echo "[preflight] checking GPG & key files..."
( gpg --version >/dev/null 2>&1 || apt -y install gnupg >/dev/null 2>&1 ) || true
mkdir -p /opt/solbot/keys || true
if [ ! -f /opt/solbot/keys/id.json.gpg ] && [ -f /root/id.json ]; then
  echo "[preflight] encrypting /root/id.json -> /opt/solbot/keys/id.json.gpg"
  gpg --batch --yes --quick-generate-key "Solbot Deploy <ops@local>" || true
  gpg --batch --yes --encrypt --recipient "Solbot Deploy" --output /opt/solbot/keys/id.json.gpg /root/id.json || true
  shred -u /root/id.json || true
fi
echo "[preflight] checking Redis..."
( systemctl enable --now redis-server >/dev/null 2>&1 || true )
echo "[preflight] done."

echo "[preflight] Base currency: ${BASE_ASSET:-USDC}; Gas reserve SOL: ${GAS_RESERVE_SOL:-0.8}"

# Auto-convert scheduler (runs every 5 minutes; reads AUTO_CONVERT_MODE/HOUR)
( crontab -l 2>/dev/null | grep -v convert_scheduler.sh ; echo '*/5 * * * * /bin/bash -lc "cd $HOME/solbot && ./scripts/convert_scheduler.sh" >> /var/log/solbot_cron.log 2>&1' ) | crontab -

# ensure .env exists (use balanced preset by default)
if [ ! -f .env ]; then
  if [ -f configs/.env.preset.balanced ]; then
    cp configs/.env.preset.balanced .env
    echo "[autorun] created .env from balanced preset"
  elif [ -f .env.example ]; then
    cp .env.example .env
    echo "[autorun] created .env from example"
  else
    touch .env
    echo "AUTO_CONVERT_MODE=off" >> .env
    echo "AUTO_CONVERT_HOUR=7" >> .env
    echo "[autorun] created empty .env with safe defaults"
  fi
fi

# Daily PnL summary at 07:00 Vietnam time
( crontab -l 2>/dev/null | grep -v pnl_daily_summary.sh ; echo '0 7 * * * TZ=Asia/Ho_Chi_Minh /bin/bash -lc "cd $HOME/solbot && ./scripts/pnl_daily_summary.sh" >> /var/log/solbot_cron.log 2>&1' ) | crontab -

# start metrics daemon (panel p50/p95, wr, pnl)
tmux new-session -d -s solbot_metrics "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u analytics/metrics_daemon.py >> logs/metrics_daemon.log 2>&1"
# start cap daemon
tmux new-session -d -s solbot_caps "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/cap_daemon.py >> logs/cap_daemon.log 2>&1"

# Block fullness probe (writes hsbot:block_fullness & hsbot:jito:tip_mult)
tmux new-session -d -s solbot_block "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/block_fullness_probe.py >> logs/block_probe.log 2>&1"
# Relay scoring every minute
( crontab -l 2>/dev/null | grep -v relay_scoring.sh ; echo '* * * * * /bin/bash -lc "cd $HOME/solbot && ./scripts/relay_scoring.sh" >> /var/log/solbot_cron.log 2>&1' ) | crontab -

# Pacing daemon
tmux new-session -d -s solbot_pacer "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/pacing_daemon.py >> logs/pacing.log 2>&1"
# Relay blacklist cron
( crontab -l 2>/dev/null | grep -v relay_blacklist.sh ; echo '* * * * * /bin/bash -lc "cd $HOME/solbot && ./scripts/relay_blacklist.sh" >> /var/log/solbot_cron.log 2>&1' ) | crontab -

# Relay health daemon (dynamic TTL blacklist by fail-frequency)
tmux new-session -d -s solbot_rhealth "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/relay_health_daemon.py >> logs/relay_health.log 2>&1"

# RPC rotator
tmux new-session -d -s solbot_rpc "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/rpc_rotator.py >> logs/rpc_rotator.log 2>&1"
# Relay success ratio
tmux new-session -d -s solbot_rratio "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/relay_health_ratio.py >> logs/relay_ratio.log 2>&1"
# PnL-by-route logger
tmux new-session -d -s solbot_pnlroute "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u analytics/pnl_routes.py >> logs/pnl_routes.log 2>&1"
# Auto-heal cron
( crontab -l 2>/dev/null | grep -v heal_daemon.sh ; echo '*/1 * * * * /bin/bash -lc "cd $HOME/solbot && ./scripts/heal_daemon.sh" >> /var/log/solbot_cron.log 2>&1' ) | crontab -

# RPC force router (HTTP, 127.0.0.1:8899) & watcher
tmux new-session -d -s solbot_rpcrtr "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/rpc_force_router.py >> logs/rpc_router.log 2>&1"
tmux new-session -d -s solbot_rpcwatch "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/rpc_current_watch.py >> logs/rpc_watch.log 2>&1"
# Ensure ENV override for child sessions (non-destructive append if missing)
grep -q '^RPC_URL=' .env 2>/dev/null || echo 'RPC_URL=http://127.0.0.1:8899' >> .env
grep -q '^SOLANA_RPC_URL=' .env 2>/dev/null || echo 'SOLANA_RPC_URL=http://127.0.0.1:8899' >> .env
export RPC_URL=http://127.0.0.1:8899
export SOLANA_RPC_URL=http://127.0.0.1:8899

# WS force router and watcher
tmux new-session -d -s solbot_wsrtr "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/ws_force_router.py >> logs/ws_router.log 2>&1"
tmux new-session -d -s solbot_wswatch "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/ws_current_watch.py >> logs/ws_watch.log 2>&1"
# Ensure WS env
grep -q '^WS_URL=' .env 2>/dev/null || echo 'WS_URL=ws://127.0.0.1:8900' >> .env
grep -q '^SOLANA_WS_URL=' .env 2>/dev/null || echo 'SOLANA_WS_URL=ws://127.0.0.1:8900' >> .env
export WS_URL=ws://127.0.0.1:8900
export SOLANA_WS_URL=ws://127.0.0.1:8900
# Disk guard every 15 minutes
( crontab -l 2>/dev/null | grep -v disk_guard.sh ; echo '*/15 * * * * /bin/bash -lc "cd $HOME/solbot && ./scripts/disk_guard.sh" >> /var/log/solbot_cron.log 2>&1' ) | crontab -

# WS error watcher
tmux new-session -d -s solbot_wserr "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/ws_error_watch.py >> logs/ws_error.log 2>&1"

# PnL watch
tmux new-session -d -s solbot_pnlw "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/pnl_watch.py >> logs/pnl_watch.log 2>&1"

# Daily stop-loss watcher
tmux new-session -d -s solbot_stoploss "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; BASE_EQUITY_USD=${BASE_EQUITY_USD:-10000} STOPLOSS_DAILY_PCT=${STOPLOSS_DAILY_PCT:-3} python3 -u scripts/stoploss_watch.py >> logs/stoploss.log 2>&1"

# Daily summary 7AM VN
tmux new-session -d -s solbot_dailysum "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; python3 -u scripts/daily_summary.py >> logs/daily_summary.log 2>&1"

# Daily take-profit watcher
tmux new-session -d -s solbot_stopgain "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; BASE_EQUITY_USD=${BASE_EQUITY_USD:-10000} STOPGAIN_DAILY_PCT=${STOPGAIN_DAILY_PCT:-10} python3 -u scripts/stopgain_watch.py >> logs/stopgain.log 2>&1"

# Daily USDC rebalance (23:59 VN)
tmux new-session -d -s solbot_rebalance "cd $HOME/solbot && . ./.venv/bin/activate 2>/dev/null || true; REBALANCE_NONUSDC_THRESHOLD_PCT=${REBALANCE_NONUSDC_THRESHOLD_PCT:-5} python3 -u scripts/rebalance_daily.py >> logs/rebalance.log 2>&1"

# Rebalance defaults (non-destructive)
export REBAL_SLIPPAGE_BPS=${REBAL_SLIPPAGE_BPS:-50}
export REBAL_TIP_LAMPORTS=${REBAL_TIP_LAMPORTS:-0}


# log rotate (safe, tiny)
mkdir -p logs
for f in logs/*.log; do
  [ -f "$f" ] || continue
  sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  if [ "$sz" -gt $((10*1024*1024)) ]; then
    mv "$f" "$f.$(date +%s).old"
  fi
done


# Start global failover watchdog (best p95)
tmux new-session -d -s solbot_watchdog "cd $HOME/solbot && FAILOVER_WATCH_INTERVAL=${FAILOVER_WATCH_INTERVAL:-15} RPC_CANDIDATES=\"${RPC_CANDIDATES}\" JITO_RELAYS_CANDIDATES=\"${JITO_RELAYS_CANDIDATES}\" bash scripts/failover_watchdog.sh >> logs/watchdog.log 2>&1"


echo "[*] Running self-check..."
bash scripts/selfcheck.sh || true
if [ -f .selfcheck_status ]; then
  echo "[*] Self-check status: $(cat .selfcheck_status)"
fi

tmux new-session -d -s solbot_jito "source .venv/bin/activate && python3 -m adapters.jito_submitter >> logs/solbot_jito.log 2>&1 || true"

tmux new-session -d -s solbot_backrun "source .venv/bin/activate && python3 -m core.backrun_engine >> logs/solbot_backrun.log 2>&1 || true"

# Launch risk guard
tmux new-session -d -s solbot_risk 'python3 scripts/risk_guard.py >> logs/risk_guard.log 2>&1'


# launch pnl-by-route aggregator
tmux new-session -d -s solbot_pnlagg "source .venv/bin/activate && python3 scripts/pnl_by_route_agg.py >> logs/pnl_by_route.log 2>&1"

# launch daily summary (07:00 VN)
tmux new-session -d -s solbot_daily "source .venv/bin/activate && python3 scripts/daily_summary_vn.py >> logs/daily_summary.log 2>&1"

# launch guarded bootstrap
tmux new-session -d -s solbot_guard "source .venv/bin/activate && python3 scripts/guarded_bootstrap.py >> logs/guarded_bootstrap.log 2>&1"


# launch pnl/day timeseries writer
tmux new-session -d -s solbot_pnlts "source .venv/bin/activate && python3 scripts/pnl_day_timeseries.py >> logs/pnl_day_timeseries.log 2>&1"

# launch auto-heal supervisor
tmux new-session -d -s solbot_autoheal "bash scripts/autoheal.sh >> logs/autoheal.log 2>&1"


# launch daily log rotation at 00:01 VN
tmux new-session -d -s solbot_logrot "bash scripts/logrotate_vn_daily.sh >> logs/logrotate.log 2>&1"


# launch csv rotation/retention
tmux new-session -d -s solbot_csvrot "bash scripts/rotate_csv_daily.sh >> logs/rotate_csv.log 2>&1"


# smoke test panel APIs (non-blocking)
bash scripts/smoke_test.sh >> logs/smoke_test.log 2>&1 || true


# launch panel health watcher
tmux new-session -d -s solbot_health "source .venv/bin/activate && python3 scripts/panel_health_watch.py >> logs/health_watch.log 2>&1"


# --- sysctl/kernel tuning (safe defaults) ---
echo "[autorun] Applying kernel/network tuning..."
cat <<'EOF' >/etc/sysctl.d/99-solbot.conf
net.ipv4.tcp_tw_reuse=1
net.core.somaxconn=1024
net.ipv4.tcp_fin_timeout=10
EOF
sysctl --system >/dev/null 2>&1 || true
systemctl enable --now irqbalance >/dev/null 2>&1 || true

# --- apply apparmor profiles if available ---
if [ -x ./scripts/apparmor_apply.sh ]; then
  ./scripts/apparmor_apply.sh || true
fi


echo "[autorun] Preflight (env & keys)"
need=0
for k in WALLET_PUBKEY RPC_CANDIDATES JITO_RELAYS_CANDIDATES; do
  if ! grep -q "^$k=" .env 2>/dev/null; then echo " - Missing $k" ; need=1; fi
done
if [ ! -f /opt/solbot/keys/id.json.gpg ]; then echo " - Missing /opt/solbot/keys/id.json.gpg"; need=1; fi
if [ "$need" = "1" ]; then echo "[autorun] Missing critical items. Wizard will guide you."; fi

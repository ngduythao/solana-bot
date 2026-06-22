#!/usr/bin/env bash
set -euo pipefail

# One-click runner for solbot: choose a preset and go.
# Usage:
#   ./scripts/oneclick.sh                # default: balanced
#   ./scripts/oneclick.sh bluechips
#   ./scripts/oneclick.sh memecoins

PROFILE="${1:-balanced}"

if [ "${PROFILE}" = "auto" ]; then
  echo "[*] oneclick: measuring RTT and auto-selecting profile..."
  exec "$(dirname "$0")/auto_profile.sh"
fi
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[*] solbot one-click starting (profile: $PROFILE)"

# 0) basic deps
if ! command -v python3 >/dev/null; then
  echo "python3 not found"; exit 1
fi
if ! command -v redis-cli >/dev/null; then
  echo "redis-cli not found (apt install redis-tools)"; fi
if ! command -v gpg >/dev/null; then
  echo "gpg not found (apt install gnupg)"; fi

# 1) install
./scripts/install_ubuntu24.sh

# 2) .env
if [ ! -f .env ]; then
  cp .env.example .env || true
fi
PRESET="configs/.env.preset.$PROFILE"
if [ -f "$PRESET" ]; then
  echo "[*] applying preset $PRESET into .env (non-destructive append)"
  cat "$PRESET" >> .env
else
  echo "[!] preset $PROFILE not found, using current .env"
fi

# 3) preflight
./scripts/preflight_guard.sh || true

# 4) run
./scripts/run_all.sh

echo
echo "[✓] solbot is launching. Tips:"
echo "    - tail -f logs/* or tmux a -t solbot_*"
echo "    - python3 -m analytics.panel_latency_pnl"
echo "    - tools/hedge_ctl.sh set prio_mult SOL 0.8"


# Extra: equinix-tuned (runs network tuning & MTU & chrony first)
if [ "${PROFILE}" = "equinix-tuned" ]; then
  echo "[*] Applying Equinix-tuned net settings (sudo required)..."
  sudo ./scripts/net_tune.sh || true
  sudo IFACES="${IFACES:-eth0}" MTU="${MTU:-9000}" ./scripts/setup_mtu.sh || true
  sudo ./scripts/setup_chrony.sh || true
fi


# Extra hooks for equinix-tuned: CPU pin & watchdog timer
if [ "${PROFILE}" = "equinix-tuned" ]; then
  echo "[*] (Optional) CPU pin critical processes (set CPU_PIN='2-5' before run)"
  CPU_PIN="${CPU_PIN:-}" ./scripts/cpu_pin.sh || true
  echo "[*] (Optional) Install systemd watchdog timer (sudo)"
  sudo ./scripts/setup_watchdog_timer.sh || true
fi


# Launch auto-failover agent if enabled
if [ "${FAILOVER_ENABLE:-1}" = "1" ]; then
  echo "[*] starting auto-failover agent (tmux: solbot_failover)"
  CURRENT_PROFILE="${PROFILE}" tmux new-session -d -s solbot_failover 'cd "$(dirname "$0")/.." && exec ./scripts/auto_failover.sh'
fi

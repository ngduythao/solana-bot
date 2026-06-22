
#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "[ONE-CLICK] Detected OS:" $(lsb_release -ds || cat /etc/os-release | head -n1)
echo "[ONE-CLICK] Updating apt and installing base deps"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git curl tmux redis-server jq ufw

# Open ports for dashboards
sudo ufw allow 8080/tcp || true
sudo ufw allow 8081/tcp || true

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$BASE_DIR/solana-bot"

cd "$APP_DIR"
if [ ! -d ".venv" ]; then
  echo "[ONE-CLICK] Creating venv"
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip

REQ_FILE="requirements_min.txt"
[ -f requirements.txt ] && REQ_FILE="requirements.txt"
echo "[ONE-CLICK] Installing python deps from $REQ_FILE"
pip install -r "$REQ_FILE"

# Bootstrap .env if missing
if [ ! -f ".env" ]; then
  echo "[ONE-CLICK] Writing .env (sample)"
  cat > .env <<EOF
REDIS_URL=redis://localhost:6379/0
RPC_PRIMARY=https://api.mainnet-beta.solana.com
TIP_STREAM_URL=wss://bundles.jito.wtf/api/v1/bundles/tip_stream
TIP_FLOOR_URL=https://bundles.jito.wtf/api/v1/bundles/tip_floor
JITO_RELAYS=singapore.mainnet.block-engine.jito.wtf,tokyo.mainnet.block-engine.jito.wtf

FEE_MIN_TIP_LAMPORTS=1000
FEE_ALPHA=1.5
FEE_BETA_LAT=0.15
FEE_GAMMA_ACC=0.25
FEE_DELTA_P95=0.10

ANTIPVP_SPLITS=3
ANTIPVP_STAGGER_MS=4

ADAPTER_PRESETS=adapters/presets.yaml
EOF
fi

echo "[ONE-CLICK] Running env validator"
python services/env_validator.py || true
python services/env_schema_strict.py || true
python services/health_server.py &
python services/queue_gc.py &

# Enable and start Redis if not running
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install systemd services (auto 24/7)
echo "[ONE-CLICK] Installing systemd units"
sudo bash deploy/install_systemd.sh

echo "[ONE-CLICK] Done. (IP HINT below)"
IP=$(hostname -I 2>/dev/null | awk "{print $1}") || true
[ -z "$IP" ] && IP=$(curl -s ifconfig.me || true)
echo "Server IP: ${IP:-<your-ip>}"; echo "Dashboards: http://$IP:8080  and  http://$IP:8081/pro"
echo "[ONE-CLICK] You can watch logs:"
echo "  journalctl -u solbot_core@$(logname) -f"
echo "Dashboards: http://<server-ip>:8080 and http://<server-ip>:8081/pro"


# Optional: load system-wide secrets
sudo mkdir -p /etc/solbot
if [ -f /etc/solbot/.env ]; then
  echo "[ONE-CLICK] Detected /etc/solbot/.env for secrets"
fi


echo "[ONE-CLICK] Auto-fetching popular markets (best-effort)"
python solana-bot/adapters/auto_fetch_markets.py || true

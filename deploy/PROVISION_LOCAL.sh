
#!/usr/bin/env bash
# Provision a single server locally (run ON the server) for a chosen region.
# Usage: sudo bash deploy/PROVISION_LOCAL.sh nj|sg [username]
set -euo pipefail
REGION="${1:-nj}"
LOGIN_USER="${2:-$(logname || echo $SUDO_USER)}"
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi

echo "[PROVISION_LOCAL] region=$REGION user=$LOGIN_USER"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl tmux redis-server jq ufw

# Firewall
ufw allow OpenSSH || true
ufw allow 8080/tcp || true
ufw allow 8081/tcp || true
ufw allow 9090/tcp || true
ufw allow 7080/tcp || true
yes | ufw enable || true

# Ensure ownership
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
chown -R "$LOGIN_USER":"$LOGIN_USER" "$BASE_DIR"

# Region env
cd "$BASE_DIR"
if [[ "$REGION" == "nj" ]]; then
  cp solana-bot/deploy/env.sample.nj .env
else
  cp solana-bot/deploy/env.sample.sg .env
fi

# One-click
sudo -u "$LOGIN_USER" bash -c 'cd '"$BASE_DIR"'/solana-bot/.. && bash solana-bot/deploy/ONE_CLICK_INSTALL.sh'

echo "[PROVISION_LOCAL] Done. Dashboards:"
IP=$(hostname -I | awk '{print $1}')
echo "  http://$IP:8080   http://$IP:8081/pro   health: http://$IP:9090/ready"

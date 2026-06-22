
#!/usr/bin/env bash
# Provision TWO servers from your laptop: New Jersey and Singapore.
# Requires: ssh/scp access with a key. Zip path: solbot66_upgrade.zip or newer.
#
# Usage:
#   bash deploy/PROVISION_REMOTE.sh <NJ_IP> <SG_IP> <SSH_USER> <SSH_KEY> <PATH_TO_ZIP>
#
set -euo pipefail
NJ_IP="${1:-}"; SG_IP="${2:-}"; SSH_USER="${3:-root}"; SSH_KEY="${4:-~/.ssh/id_rsa}"; ZIP="${5:-solbot66_upgrade.zip}"
if [[ -z "$NJ_IP" || -z "$SG_IP" || -z "$ZIP" ]]; then
  echo "Usage: bash deploy/PROVISION_REMOTE.sh <NJ_IP> <SG_IP> <SSH_USER> <SSH_KEY> <PATH_TO_ZIP>"; exit 1; fi

function setup_host(){
  local IP="$1"; local REGION="$2"
  echo "[REMOTE] Copy zip to $IP ($REGION)"
  scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$ZIP" "$SSH_USER@$IP:/root/"
  echo "[REMOTE] Install & run one-click on $IP"
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$IP" bash -s <<'EOS'
set -euo pipefail
ZIP=$(ls -1 *.zip 2>/dev/null | head -n1 || true)
if [[ -z "$ZIP" ]]; then echo "No zip found"; exit 1; fi
apt-get update -y && apt-get install -y unzip
unzip -o "$ZIP"
cd solanabot_release/*/solana-bot/..
# region marker injected at runtime
if echo "$ZIP" | grep -q "solbot66"; then true; fi
EOS
  # region-specific .env and provision local
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$IP" bash -s <<EOS
set -euo pipefail
cd solanabot_release/*/solana-bot/..
if [[ "$REGION" == "nj" ]]; then
  cp solana-bot/deploy/env.sample.nj .env
else
  cp solana-bot/deploy/env.sample.sg .env
fi
sudo bash solana-bot/deploy/PROVISION_LOCAL.sh "$REGION" "$SSH_USER"
EOS
}

setup_host "$NJ_IP" "nj"
setup_host "$SG_IP" "sg"

echo "[REMOTE] All done. Open dashboards at:"
echo "  NJ: http://$NJ_IP:8080   http://$NJ_IP:8081/pro"
echo "  SG: http://$SG_IP:8080   http://$SG_IP:8081/pro"

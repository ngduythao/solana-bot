
#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$BASE_DIR/deploy/ENV_FINAL_TEMPLATE.env"

sudo mkdir -p /etc/solbot
sudo cp "$SRC" /etc/solbot/.env
sudo chown root:root /etc/solbot/.env
sudo chmod 600 /etc/solbot/.env
echo "[ENV] /etc/solbot/.env installed from template."
echo "[ENV] Now set MAKER_KEYPAIR path and any Jito creds if you have them."

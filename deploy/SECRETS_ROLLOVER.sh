
#!/usr/bin/env bash
set -euo pipefail
# Rotate secrets: copy new .env to /etc/solbot/.env with backup and perms; rotate keypair if provided
sudo mkdir -p /etc/solbot
if [ -f ".env" ]; then
  sudo cp .env /etc/solbot/.env
  sudo chown root:root /etc/solbot/.env
  sudo chmod 600 /etc/solbot/.env
  echo "[secrets] /etc/solbot/.env updated"
fi
if [ -n "${1-}" ]; then
  KP="$1"
  sudo install -m 600 "$KP" /etc/solbot/maker.json
  echo "MAKER_KEYPAIR=/etc/solbot/maker.json"
fi

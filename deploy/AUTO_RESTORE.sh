
#!/usr/bin/env bash
set -euo pipefail
DIR="/var/backups/solbot"
LATEST=$(ls -1t "$DIR"/snapshot-*.tgz 2>/dev/null | head -n1 || true)
if [ -z "$LATEST" ]; then echo "[RESTORE] No snapshot found"; exit 0; fi
echo "[RESTORE] Using $LATEST"
TMP=$(mktemp -d)
tar -xzf "$LATEST" -C "$TMP" || exit 0
if [ -f "$TMP/etc/solbot/.env" ]; then
  sudo mkdir -p /etc/solbot
  sudo cp "$TMP/etc/solbot/.env" /etc/solbot/.env
  sudo chmod 600 /etc/solbot/.env
fi
echo "[RESTORE] Done"

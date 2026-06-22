
#!/usr/bin/env bash
set -euo pipefail
echo "[FIX] Patching installed systemd unit files (remove invalid 'source' lines)"
shopt -s nullglob
for f in /etc/systemd/system/solbot_*.service; do
  if grep -q "/etc/solbot/hardening.conf" "$f"; then
    sudo sed -i '/hardening.conf/d' "$f"
    echo "[FIX] cleaned $f"
  fi
done
systemctl daemon-reload || true

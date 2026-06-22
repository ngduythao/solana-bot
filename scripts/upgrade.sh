#!/usr/bin/env bash
set -euo pipefail
if [[ $(id -u) -ne 0 ]]; then
  echo "Please run as root: sudo bash scripts/upgrade.sh <archive.zip>"
  exit 1
fi
ARCHIVE="${1:-}"
if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
  echo "Usage: sudo bash scripts/upgrade.sh /path/to/solbotXX.zip"
  exit 2
fi

REL_DIR="/opt/solbot_releases"
CUR_LINK="/opt/solbot_current"
mkdir -p "$REL_DIR"

VER="solbot-20250910114241"
DEST="$REL_DIR/$VER"
mkdir -p "$DEST"
unzip -q "$ARCHIVE" -d "$DEST"
# If archive contains a top folder, flatten into $DEST
if [[ $(ls -1 "$DEST" | wc -l) -eq 1 ]]; then
  inner="$DEST/$(ls -1 "$DEST")"
  shopt -s dotglob
  mv "$inner"/* "$DEST"/
  rmdir "$inner"
fi

# Preserve .env and wallet if existing
if [[ -L "$CUR_LINK" || -d "$CUR_LINK" ]]; then
  if [[ -f "$CUR_LINK/.env" ]]; then cp "$CUR_LINK/.env" "$DEST/.env"; fi
  if [[ -d "$CUR_LINK/wallet" ]]; then mkdir -p "$DEST/wallet"; cp -a "$CUR_LINK/wallet/." "$DEST/wallet/"; fi
fi

ln -sfn "$DEST" "$CUR_LINK"
# Install or update systemd service to point at CUR_LINK
cat >/etc/systemd/system/solbot.service <<'EOF'
[Unit]
Description=Solbot 24/7 Runner
Wants=docker.service
After=docker.service network-online.target

[Service]
Type=exec
WorkingDirectory=/opt/solbot_current
ExecStart=/opt/solbot_current/run_all.sh
Restart=always
RestartSec=5s
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable solbot.service
systemctl restart solbot.service

# Cleanup old releases, keep 5 recent
cd "$REL_DIR"
ls -1dt solbot-* | tail -n +6 | xargs -r rm -rf

echo "Upgrade done. Current -> $CUR_LINK"
echo "Logs: journalctl -u solbot -f"

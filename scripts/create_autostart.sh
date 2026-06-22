#!/usr/bin/env bash
set -euo pipefail
PROFILE="${1:-auto}"
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/solbot-autostart@.service <<'UNIT'
[Unit]
Description=solbot oneclick
After=default.target
[Service]
Type=simple
WorkingDirectory=%h/solbot
ExecStart=%h/solbot/scripts/oneclick.sh %i
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now solbot-autostart@${PROFILE}.service || true
loginctl enable-linger $USER || true
echo "[✓] Enabled autostart for profile: ${PROFILE}"

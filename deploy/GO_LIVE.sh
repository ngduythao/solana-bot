
#!/usr/bin/env bash
set -euo pipefail

echo "[GO_LIVE] Applying final checks..."
bash "$(dirname "$0")/CHECKLIST.sh" || true

echo "[GO_LIVE] Enabling alerts & timers"
systemctl daemon-reload || true

# Install/enable alerts service
cat >/etc/systemd/system/solbot_alerts.service <<'EOF'
[Unit]
Description=Solbot Telegram Alerts
After=network-online.target

[Service]
WorkingDirectory=%h/solanabot_release/*/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=%h/solanabot_release/*/solana-bot/.venv/bin/python services/telegram_alerts.py
Restart=always
RestartSec=5
User=%I
EOF

# Timers for snapshot & rotate
cat >/etc/systemd/system/solbot_rotate.service <<'EOF'
[Unit]
Description=Solbot Log Rotate

[Service]
Type=oneshot
ExecStart=/bin/bash %h/solanabot_release/*/solana-bot/deploy/LOG_ROTATE.sh
User=%I
EOF

cat >/etc/systemd/system/solbot_rotate.timer <<'EOF'
[Unit]
Description=Run Solbot Log Rotate hourly
[Timer]
OnCalendar=hourly
Persistent=true
[Install]
WantedBy=timers.target
EOF

cat >/etc/systemd/system/solbot_snapshot.service <<'EOF'
[Unit]
Description=Solbot Snapshot

[Service]
Type=oneshot
ExecStart=/bin/bash %h/solanabot_release/*/solana-bot/deploy/SNAPSHOT.sh
User=%I
EOF

cat >/etc/systemd/system/solbot_snapshot.timer <<'EOF'
[Unit]
Description=Run Solbot Snapshot every 6 hours
[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true
[Install]
WantedBy=timers.target
EOF

login_user="$(logname 2>/dev/null || echo $SUDO_USER)"
systemctl enable solbot_alerts@${login_user} || true
systemctl start  solbot_alerts@${login_user} || true
systemctl enable solbot_rotate.timer || true
systemctl start  solbot_rotate.timer || true
systemctl enable solbot_snapshot.timer || true
systemctl start  solbot_snapshot.timer || true

echo "[GO_LIVE] Done. Alerts/timers active. Review /var/log/solbot and /var/backups/solbot"

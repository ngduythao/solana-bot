#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo "[!] setup_watchdog_timer.sh requires sudo"; exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="/etc/systemd/system"

cat > "$UNIT_DIR/solbot-watchdog.service" <<EOF
[Unit]
Description=Solbot watchdog

[Service]
Type=oneshot
WorkingDirectory=%h
ExecStart=$ROOT_DIR/scripts/watchdog.sh
User=%i
Group=%i
EOF

cat > "$UNIT_DIR/solbot-watchdog.timer" <<EOF
[Unit]
Description=Run Solbot watchdog every minute

[Timer]
OnCalendar=*:0/1
AccuracySec=5s
Unit=solbot-watchdog.service
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now solbot-watchdog.timer || true
systemctl list-timers | grep solbot-watchdog || true
echo "[✓] Watchdog timer installed and enabled."

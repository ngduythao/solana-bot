
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi

apt-get update -y
apt-get install -y redis-server
systemctl enable redis-server --now || true

echo "[24x7] Enabling Redis AOF persistence"
if grep -q '^appendonly no' /etc/redis/redis.conf 2>/dev/null; then
  sed -i 's/^appendonly no/appendonly yes/' /etc/redis/redis.conf || true
  systemctl restart redis-server || true
fi

echo "[24x7] Enabling persistent journald"
mkdir -p /var/log/journal
sed -i 's/^#*Storage=.*/Storage=persistent/' /etc/systemd/journald.conf || true
systemctl restart systemd-journald || true

echo "[24x7] Ensuring time sync"
timedatectl set-ntp true || true
systemctl enable systemd-timesyncd --now || true

echo "[24x7] Enabling unattended-upgrades (security)"
apt-get update -y && apt-get install -y unattended-upgrades || true
dpkg-reconfigure -fnoninteractive unattended-upgrades || true

echo "[24x7] Installing boot watchdog systemd unit"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cat >/etc/systemd/system/solbot_boot.service <<EOF
[Unit]
Description=Solbot boot watchdog
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/boot_watchdog.py
Restart=always
RestartSec=5
User=%I
. /etc/solbot/hardening.conf

[Install]
WantedBy=multi-user.target
EOF

systemctl enable solbot_boot@${SUDO_USER} || systemctl enable solbot_boot@${USER}
systemctl start  solbot_boot@${SUDO_USER} || systemctl start  solbot_boot@${USER}

echo "[24x7] Enabling plan executor systemd unit"
cat >/etc/systemd/system/solbot_planexec.service <<EOF
[Unit]
Description=Solbot plan executor
After=network-online.target redis-server.service
Wants=network-online.target

[Service]
WorkingDirectory=$BASE_DIR/solana-bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BASE_DIR/solana-bot/.venv/bin/python services/plan_executor.py
Restart=always
RestartSec=5
User=%I
. /etc/solbot/hardening.conf

[Install]
WantedBy=multi-user.target
EOF

systemctl enable solbot_planexec@${SUDO_USER} || systemctl enable solbot_planexec@${USER}
systemctl start  solbot_planexec@${SUDO_USER} || systemctl start  solbot_planexec@${USER}

echo "[24x7] Done."

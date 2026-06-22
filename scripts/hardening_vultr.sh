#!/usr/bin/env bash
set -euo pipefail

echo "[1/8] Update & base tools"
sudo apt update && sudo apt -y upgrade
sudo apt -y install curl git unzip jq ufw fail2ban 

echo "[2/8] Enable firewall (only SSH + optional 8080 local)"
sudo ufw allow OpenSSH
# Uncomment next line ONLY if you must expose dashboard publicly (not recommended)
# sudo ufw allow 8080/tcp
yes | sudo ufw enable

echo "[3/8] Docker Engine + Compose"
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER || true

echo "[4/8] Swapfile 4G (for small instances)"
if [ ! -f /swapfile ]; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "[5/8] Sysctl tuning (network & file limits)"
sudo bash -c 'cat >/etc/sysctl.d/99-solbot.conf <<EOF
net.core.somaxconn = 1024
net.ipv4.tcp_syncookies = 1
net.ipv4.ip_local_port_range = 1024 65000
fs.file-max = 1000000
net.core.netdev_max_backlog = 4096
EOF'
sudo sysctl --system

echo "[6/8] Fail2ban basic"
sudo bash -c 'cat >/etc/fail2ban/jail.d/sshd.local <<EOF
[sshd]
enabled = true
bantime = 1h
findtime = 10m
maxretry = 5
EOF'
sudo systemctl enable --now fail2ban

echo "[7/8] Unattended upgrades (security)"
sudo apt -y install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

echo "[8/8] Done. Re-login to activate docker group if needed."
echo "TIP: use SSH port forwarding for dashboard: ssh -L 8080:localhost:8080 user@server"

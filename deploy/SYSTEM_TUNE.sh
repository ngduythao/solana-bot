
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
apt-get update -y
apt-get install -y chrony ethtool

# sysctl networking for low-latency
cat >/etc/sysctl.d/99-solbot.conf <<'EOF'
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 87380 134217728
net.ipv4.tcp_wmem=4096 65536 134217728
net.core.netdev_max_backlog=250000
net.ipv4.tcp_congestion_control=bbr
net.ipv4.tcp_fastopen=3
EOF
sysctl --system || true

# chrony time sync
systemctl enable chrony || true
systemctl restart chrony || true
echo "[TUNE] sysctl + chrony applied"

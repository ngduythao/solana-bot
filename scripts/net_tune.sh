#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo "[!] net_tune.sh should run as root (sudo)"; exit 0
fi

echo "[*] Applying sysctl tuning for low-latency networking..."
cat >/etc/sysctl.d/99-solbot.conf <<'CONF'
net.core.netdev_max_backlog = 65536
net.core.somaxconn = 65535
net.core.rmem_max = 268435456
net.core.wmem_max = 268435456
net.ipv4.tcp_rmem = 4096 87380 268435456
net.ipv4.tcp_wmem = 4096 65536 268435456
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_syncookies = 0
net.ipv4.ip_local_port_range = 1024 65535
vm.swappiness = 5
fs.file-max = 1000000
CONF
sysctl --system >/dev/null || true

echo "[*] Setting ulimits..."
ulfile="/etc/security/limits.d/99-solbot.conf"
grep -q "nofile" "$ulfile" 2>/dev/null || cat >>"$ulfile" <<'LIM'
* soft nofile 1000000
* hard nofile 1000000
LIM

echo "[*] Ensuring irqbalance..."
apt-get update -y >/dev/null 2>&1 || true
apt-get install -y irqbalance >/dev/null 2>&1 || true
systemctl enable --now irqbalance >/dev/null 2>&1 || true

echo "[*] CPU governor performance..."
apt-get install -y linux-tools-common linux-tools-generic >/dev/null 2>&1 || true
which cpupower >/dev/null 2>&1 && cpupower frequency-set -g performance || true

echo "[*] Done net_tune."

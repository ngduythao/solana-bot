#!/usr/bin/env bash
# Tune kernel/network/limits for low-latency trading on Vultr (NJ). Safe defaults, LinuxPatch-friendly.
set -euo pipefail
if [[ $(id -u) -ne 0 ]]; then echo "Run as root: sudo bash scripts/tune_nj_vultr.sh"; exit 1; fi

echo "[1/6] Sysctl networking (BBR, fq, backlog, tcp opts)"
cat >/etc/sysctl.d/99-solbot.conf <<'EOF'
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 16384
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_sack = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
EOF
sysctl --system || true

echo "[2/6] File descriptor limits"
cat >/etc/security/limits.d/99-solbot.conf <<'EOF'
* soft nofile 1048576
* hard nofile 1048576
root soft nofile 1048576
root hard nofile 1048576
EOF
mkdir -p /etc/systemd/system/docker.service.d
cat >/etc/systemd/system/docker.service.d/limits.conf <<'EOF'
[Service]
LimitNOFILE=1048576
EOF
systemctl daemon-reload || true
systemctl restart docker || true

echo "[3/6] Time sync (chrony)"
apt update -y && apt install -y chrony
sed -i 's/^pool .*/pool pool.ntp.org iburst/' /etc/chrony/chrony.conf || true
systemctl enable --now chrony

echo "[4/6] CPU governor performance (if available)"
if command -v cpupower >/dev/null 2>&1; then
  cpupower frequency-set -g performance || true
else
  apt install -y linux-tools-common linux-tools-generic || true
  command -v cpupower >/dev/null 2>&1 && cpupower frequency-set -g performance || true
fi

echo "[5/6] Timezone America/New_York (NJ region)"
timedatectl set-timezone America/New_York || true

echo "[6/6] Kernel params applied. Reboot recommended to fully take effect."
echo "→ Consider scheduling reboot via LinuxPatch UI; service will auto-start after reboot."


#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
cat >/etc/sysctl.d/98-solbot-lowlat.conf <<'EOF'
net.ipv4.tcp_timestamps=0
net.ipv4.tcp_sack=1
net.ipv4.tcp_low_latency=1
net.core.busy_poll=50
net.core.busy_read=50
net.core.somaxconn=4096
EOF
sysctl --system || true

# CPU governor performance
if command -v cpupower >/dev/null 2>&1; then
  cpupower frequency-set -g performance || true
fi

echo "[LOWLAT] applied minimal low-latency kernel/NIC tuning"

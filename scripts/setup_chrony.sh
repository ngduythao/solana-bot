#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo "[!] setup_chrony.sh should run as root (sudo)"; exit 0
fi
apt-get update -y >/dev/null 2>&1 || true
apt-get install -y chrony >/dev/null 2>&1 || true
systemctl enable --now chrony >/dev/null 2>&1 || true
chronyc tracking || true

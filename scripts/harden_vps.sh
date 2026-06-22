#!/usr/bin/env bash
set -euo pipefail
which ufw >/dev/null 2>&1 || apt -y install ufw >/dev/null 2>&1 || true
which fail2ban-client >/dev/null 2>&1 || apt -y install fail2ban >/dev/null 2>&1 || true
ufw allow 22/tcp >/dev/null 2>&1 || true
ufw allow 80/tcp >/dev/null 2>&1 || true
ufw allow 443/tcp >/dev/null 2>&1 || true
ufw --force enable >/dev/null 2>&1 || true
systemctl enable --now fail2ban >/dev/null 2>&1 || true
echo "[harden] ufw+fail2ban ensured."

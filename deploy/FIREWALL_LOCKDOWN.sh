
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
ADMIN_IPS="${ADMIN_IP_WHITELIST:-}"
PORTS="${OPEN_PORTS:-8080,8081,9090}"
IFS=',' read -r -a arr <<< "$PORTS"
if [[ -z "$ADMIN_IPS" ]]; then
  echo "[FW] No ADMIN_IP_WHITELIST set; keeping ports closed (recommended)."
  exit 0
fi
# Close existing rules for those ports then add per-IP allow
for p in "${arr[@]}"; do
  ufw deny "$p/tcp" || true
  for ip in ${ADMIN_IPS//,/ }; do
    ufw allow from "$ip" to any port "$p" proto tcp || true
  done
done
ufw status verbose
echo "[FW] Applied allowlist for ports $PORTS to IPs: $ADMIN_IPS"

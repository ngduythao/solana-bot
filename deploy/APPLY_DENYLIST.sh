
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
REDIS_CLI="${REDIS_CLI:-redis-cli}"
LISTS=("solbot:deny:ips" "solbot:deny:abuse")
for key in "${LISTS[@]}"; do
  echo "[DENY] syncing $key"
  $REDIS_CLI SMEMBERS "$key" | while read -r ip; do
    [[ -z "$ip" ]] && continue
    ufw deny from "$ip" || true
  done
done
ufw status verbose | sed -n '1,200p'

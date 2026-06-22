#!/usr/bin/env bash
set -euo pipefail
ENABLE="${SSH_WATCH_ENABLE:-1}"
TRUST="${SSH_TRUSTED_CIDRS:-}"
[[ "$ENABLE" = "1" ]] || exit 0

log="/var/log/auth.log"
REDIS="${REDIS_URL:-redis://redis:6379/0}"

# simple tail
( tail -n0 -F "$log" ) | while read -r line; do
  if echo "$line" | grep -E "Accepted .*ssh|Failed password|authentication failure" >/dev/null; then
    ip=$(echo "$line" | grep -oE "rhost=[0-9\.]+|from [0-9\.]+ port" | grep -oE "[0-9\.]+")
    if [[ -n "$ip" ]]; then
      # You can implement CIDR trust check here (skipped for brevity)
      # Publish panic alert
      python3 - "$REDIS" "$ip" <<'PY'
import sys, json, redis
r = redis.from_url(sys.argv[1])
ip = sys.argv[2]
r.publish("hsbot:alerts", json.dumps({"type":"ssh_login","ip":ip}))
r.set("hsbot:panic", 1)
PY
    fi
  fi
done

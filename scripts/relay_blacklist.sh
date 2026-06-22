#!/usr/bin/env bash
set -euo pipefail
RELAYS="${JITO_RELAYS:-}"
[ -z "$RELAYS" ] && exit 0
IFS=',' read -ra R <<< "$RELAYS"
i=0
for rel in "${R[@]}"; do
  i=$((i+1))
  ms=$(redis-cli GET "jito:relay:rtt:${i}" 2>/dev/null)
  ms=${ms:-9999}
  if awk -v m="$ms" 'BEGIN{exit !(m+0.0>800)}'; then
    # spike: blacklist 2 minutes
    redis-cli SETEX "jito:relay:black:${i}" 120 1 >/dev/null 2>&1 || true
  fi
done

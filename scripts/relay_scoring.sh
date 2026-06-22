#!/usr/bin/env bash
set -euo pipefail
RELAYS="${JITO_RELAYS:-}"
[ -z "$RELAYS" ] && exit 0
IFS=',' read -ra R <<< "$RELAYS"
rtts=()
i=0
for rel in "${R[@]}"; do
  i=$((i+1))
  ms=$( (time -p curl -m 1 -s -o /dev/null "$rel") 2>&1 | awk '/real/{print $2*1000}' || echo 999 )
  rtts+=("$ms"); redis-cli SET "jito:relay:rtt:${i}" "$ms" >/dev/null 2>&1 || true
done
sorted=($(printf '%s\n' "${rtts[@]}" | sort -n))
n=${#sorted[@]}
p50=${sorted[$((n/2))]}
p95=${sorted[$((n*95/100))]}
redis-cli SET jito:rtt_p50 "$p50" >/dev/null 2>&1 || true
redis-cli SET jito:rtt_p95 "$p95" >/dev/null 2>&1 || true

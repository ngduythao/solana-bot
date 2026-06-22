#!/usr/bin/env bash
# scripts/failover_watchdog.sh
# Promote best-by-p95 RPC/Jito to "active" keys in Redis and optionally poke services.
set -euo pipefail
REDIS_CLI="${REDIS_CLI:-redis-cli}"
best_by_p95() {
  local prefix="$1" # rpc:rtt or jito:rtt
  local list="$2"   # comma separated
  IFS=',' read -r -a arr <<< "$list"
  local best=""; local bestp=999999999
  for x in "${arr[@]}"; do
    [ -n "$x" ] || continue
    keyify="${x//:\/\//_}"; keyify="${keyify//\//_}"; keyify="${keyify//./_}"; keyify="${keyify//:/_}"
    p95="$($REDIS_CLI get "hsbot:${prefix}:${keyify}:p95" 2>/dev/null || true)"
    [ -z "$p95" ] && p95=0
    if [ "$p95" -gt 0 ] && [ "$p95" -lt "$bestp" ]; then
      bestp="$p95"; best="$x"
    fi
  done
  echo "$best"
}

while true; do
  RPCS="${RPC_CANDIDATES:-}"
  JITOS="${JITO_RELAYS_CANDIDATES:-}"
  if [ -n "$RPCS" ]; then
    best_rpc="$(best_by_p95 "rpc:rtt" "$RPCS")"
    if [ -n "$best_rpc" ]; then
      $REDIS_CLI set hsbot:rpc:active "$best_rpc" >/dev/null
    fi
  fi
  if [ -n "$JITOS" ]; then
    best_jito="$(best_by_p95 "jito:rtt" "$JITOS")"
    if [ -n "$best_jito" ]; then
      $REDIS_CLI set hsbot:jito:active "$best_jito" >/dev/null
    fi
  fi
  sleep "${FAILOVER_WATCH_INTERVAL:-15}"
done

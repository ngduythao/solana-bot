#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CURRENT_PROFILE="${CURRENT_PROFILE:-balanced}"
CHECK_SEC="${FAILOVER_CHECK_SEC:-60}"
BAD_MS="${FAILOVER_BAD_MS:-120}"
IMPROVE_PCT="${FAILOVER_IMPROVE_PCT:-20}"
PROFILES=(${FAILOVER_PROFILES:-balanced vultr vultr-sg equinix})

score_profile() {
  local prof="$1"
  local preset="configs/.env.preset.$prof"
  [ -f "$preset" ] || { echo 999999; return; }
  local RPC=$(grep -E '^RPC_CANDIDATES=' "$preset" | head -n1 | cut -d= -f2- | tr -d '"')
  local REL=$(grep -E '^JITO_RELAYS_CANDIDATES=' "$preset" | head -n1 | cut -d= -f2- | tr -d '"')
  RPC_CANDIDATES="$RPC" JITO_RELAYS_CANDIDATES="$REL" tools/bench_net.sh > .failover_bench.out 2>/dev/null || true
  local ms=$(grep -Eo '[0-9]+ms' .failover_bench.out | tr -d 'ms' | tr '\n' ' ')
  local sum=0 cnt=0
  for v in $ms; do sum=$((sum+v)); cnt=$((cnt+1)); done
  [ "$cnt" -eq 0 ] && echo 999999 || echo $((sum/cnt))
}

echo "[*] Auto-failover agent started (check=${CHECK_SEC}s, bad>${BAD_MS}ms, improve>=${IMPROVE_PCT}%)"
while true; do
  CUR=$(score_profile "$CURRENT_PROFILE")
  BEST="$CURRENT_PROFILE"; BESTSCORE="$CUR"
  for p in "${PROFILES[@]}"; do
    [ "$p" = "$CURRENT_PROFILE" ] && continue
    sc=$(score_profile "$p")
    if [ "$sc" -lt "$BESTSCORE" ]; then BEST="$p"; BESTSCORE="$sc"; fi
  done

  if [ "$CUR" -ge "$BAD_MS" ] && [ $(( (CUR - BESTSCORE)*100 / CUR )) -ge "$IMPROVE_PCT" ]; then
    echo "[!] Failover: current=$CURRENT_PROFILE ${CUR}ms -> best=$BEST ${BESTSCORE}ms (improve >= ${IMPROVE_PCT}%)"
    CURRENT_PROFILE="$BEST"
    ./scripts/restart_stack.sh "$BEST" || true
    # restart_stack execs oneclick; if it returns, sleep a bit
    sleep "$CHECK_SEC"
  else
    echo "[*] Healthy: ${CURRENT_PROFILE} (${CUR}ms) — best alt ${BEST} (${BESTSCORE}ms)"
    sleep "$CHECK_SEC"
  fi
done

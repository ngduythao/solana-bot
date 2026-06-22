#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail

warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
ok()   { printf "\033[32m[ok]\033[0m %s\n" "$*"; }

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a

# 1) Check RPC & RELAYS
[ -z "${RPC_CANDIDATES-}" ] && warn "RPC_CANDIDATES is empty"
[ -z "${JITO_RELAYS_CANDIDATES-}" ] && warn "JITO_RELAYS_CANDIDATES is empty"

# 2) Hedge interval vs cooldown
cdl=${HEDGE_COOLDOWN_SEC:-2}
map="${HEDGE_MIN_INTERVAL_SEC_MAP:-}"
if [ -n "$map" ]; then
  IFS=',' read -ra items <<< "$map"
  for kv in "${items[@]}"; do
    mint="${kv%%:*}"; val="${kv##*:}"
    if [ "$val" -lt "$cdl" ] 2>/dev/null; then
      warn "HEDGE_MIN_INTERVAL_SEC_MAP[$mint]=$val < HEDGE_COOLDOWN_SEC=$cdl"
    fi
  done
fi

# 3) Per-mint limit vs notional
lim="${HEDGE_PER_MINT_LIMIT_USD:-}"
minnot="${HEDGE_MIN_NOTIONAL_USD:-25}"
if [ -n "$lim" ]; then
  IFS=',' read -ra items <<< "$lim"
  for kv in "${items[@]}"; do
    mint="${kv%%:*}"; val="${kv##*:}"
    if [ "$val" -lt "$minnot" ] 2>/dev/null; then
      warn "HEDGE_PER_MINT_LIMIT_USD[$mint]=$val < HEDGE_MIN_NOTIONAL_USD=$minnot"
    fi
  done
fi

# 4) Slippage max sanity
sl="${HEDGE_SLIPPAGE_BPS:-80}"
mx="${HEDGE_MAX_SLIPPAGE_BPS:-180}"
if [ "$sl" -gt "$mx" ] 2>/dev/null; then
  warn "HEDGE_SLIPPAGE_BPS=$sl > HEDGE_MAX_SLIPPAGE_BPS=$mx"
fi

ok "lint_env finished"

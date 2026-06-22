
#!/usr/bin/env bash
set -euo pipefail
REDIS_CLI=${REDIS_CLI:-redis-cli}

bold() { printf "\033[1m%s\033[0m\n" "$*"; }

bold "[ solbot config – effective view ]"
echo "Note: Redis overrides > ENV per-mint > ENV global > defaults"

show_param() {
  local param="$1"; shift
  local mints=("$@")
  local glb_env="${param}"
  echo
  bold "Param: $param"
  # global via ENV
  if [ -n "${!glb_env-}" ]; then
    echo "ENV (global): ${!glb_env}"
  fi
  # default via Redis
  local rdef=$($REDIS_CLI get "hsbot:hedge:cfg:${param,,}:default" 2>/dev/null || true)
  [ -n "$rdef" ] && echo "Redis default: $rdef"
  # per-mint
  for m in "${mints[@]}"; do
    local envm="${param}_${m}"
    local rkey="hsbot:hedge:cfg:${param,,}:$m"
    local rv=$($REDIS_CLI get "$rkey" 2>/dev/null || true)
    [ -n "$rv" ] && echo "Redis[$m]: $rv"
    if [ -n "${!envm-}" ]; then
      echo "ENV[$m]: ${!envm}"
    fi
  done
}

MINTS=(${MINTS_OVERRIDE:-SOL USDT USDC JUP BONK WIF})
show_param HEDGE_PRIO_MULT "${MINTS[@]}"
show_param HEDGE_SLIPPAGE_BPS "${MINTS[@]}"
show_param HEDGE_MAX_SLIPPAGE_BPS "${MINTS[@]}"
show_param HEDGE_MIN_NOTIONAL_USD "${MINTS[@]}"
show_param HEDGE_ONLY_USDC_OUT "${MINTS[@]}"

echo
bold "Route allow/deny (ENV)"
echo "ALLOW: ${HEDGE_ROUTE_ALLOWLIST-}"
echo "DENY : ${HEDGE_ROUTE_BLACKLIST-}"
echo
bold "Dynamic route penalties (Redis)"
$REDIS_CLI keys "hsbot:route:deny:*" | sed 's/^/ - /' || true

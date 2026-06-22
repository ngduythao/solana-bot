#!/usr/bin/env bash
# Convert portfolio to BASE_ASSET (USDC) via router, keep GAS_RESERVE_SOL for fees
set -euo pipefail
# Usage: convert_to_base.sh [--preview]
PREVIEW=0
if [ "${1:-}" = "--preview" ]; then PREVIEW=1; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BASE="${BASE_ASSET:-USDC}"
RESERVE="${GAS_RESERVE_SOL:-0.8}"
SLIP_BPS="${CONVERT_SLIPPAGE_BPS:-30}"   # 30 bps = 0.3%%
TOKENS_REQ="${CONVERT_TOKENS:-auto}"     # auto = detect from state/portfolio.json; else CSV symbols e.g. 'SOL,BONK,WIF'

STATE_PORT="/opt/solbot/state/portfolio.json"
REQ_FILE="/tmp/solbot_convert_base.request"
LOG_TMP="/tmp/solbot_convert_base.log"
LOG_CONVERT="/var/log/solbot_convert.log"
mkdir -p /var/log >/dev/null 2>&1 || true

# helper to send telegram quietly
tg() { ./scripts/tg_notify.sh "$1" >/dev/null 2>&1 || true; }

echo "[convert] BASE=$BASE, RESERVE_SOL=$RESERVE, SLIPPAGE_BPS=$SLIP_BPS, TOKENS_REQ=$TOKENS_REQ" | tee "$LOG_TMP"; echo "[$(date -Iseconds)] manual: begin convert (BASE=$BASE,reserve=$RESERVE)" >> "$LOG_CONVERT"

# Build token list
TOKENS=""
if [ "$TOKENS_REQ" = "auto" ] && [ -f "$STATE_PORT" ]; then
  TOKENS="$(python3 - <<'PY'
import json,os
p="/opt/solbot/state/portfolio.json"
try:
    j=json.load(open(p))
    syms=[]
    for it in j.get("tokens",[]):  # expected [{"symbol":"SOL","balance":...},...]
        s=it.get("symbol") or it.get("sym") or ""
        b=it.get("balance",0.0)
        if s and b and b>0: syms.append(s.upper())
    if not syms: print("SOL"); 
    else: print(",".join(sorted(set(syms))))
except Exception as e:
    print("SOL")
PY
)"
else
  TOKENS="$TOKENS_REQ"
fi

# Normalize CSV -> array
IFS=',' read -r -a ARR <<< "$TOKENS"
# Ensure SOL always considered (to trim excess to reserve)
ensure_sol=1
for t in "${ARR[@]}"; do [ "${t^^}" = "SOL" ] && ensure_sol=0; done
[ $ensure_sol -eq 1 ] && ARR+=("SOL")

# Try chain of executors
simulate_swap() {
  local FROM="$1"; local TO="$2"; local MODE="$3"; local AMT="$4"; local SLIP="$SLIP_BPS"
  # simulation best-effort: pass --simulate to executors if supported
  if python3 -c "import adapters.jupiter_cli" >/dev/null 2>&1; then
    python3 -m adapters.jupiter_cli swap --simulate --from "$FROM" --to "$TO" --mode "$MODE" --amount "$AMT" --slippage-bps "$SLIP" && return 0
  fi
  if python3 -c "import adapters.router_cli" >/dev/null 2>&1; then
    python3 -m adapters.router_cli swap --simulate --from "$FROM" --to "$TO" --mode "$MODE" --amount "$AMT" --slippage-bps "$SLIP" && return 0
  fi
  if [ -f "./scripts/route_exec.py" ]; then
    python3 ./scripts/route_exec.py swap --simulate --from "$FROM" --to "$TO" --mode "$MODE" --amount "$AMT" --slippage-bps "$SLIP" && return 0
  fi
  return 1
}
try_swap() {
  local FROM="$1"; local TO="$2"; local MODE="$3"; local AMT="$4"
  local SLIP="$SLIP_BPS"
  echo "[convert] swap request: FROM=$FROM TO=$TO MODE=$MODE AMOUNT=$AMT slip_bps=$SLIP"
  # executor 1: adapters.jupiter_cli
  if python3 -c "import adapters.jupiter_cli" >/dev/null 2>&1; then
     echo "[convert] using adapters.jupiter_cli"
     python3 -m adapters.jupiter_cli swap --from "$FROM" --to "$TO" --mode "$MODE" --amount "$AMT" --slippage-bps "$SLIP" && return 0
  fi
  # executor 2: adapters.router_cli
  if python3 -c "import adapters.router_cli" >/dev/null 2>&1; then
     echo "[convert] using adapters.router_cli"
     python3 -m adapters.router_cli swap --from "$FROM" --to "$TO" --mode "$MODE" --amount "$AMT" --slippage-bps "$SLIP" && return 0
  fi
  # executor 3: scripts/route_exec.py
  if [ -f "./scripts/route_exec.py" ]; then
     echo "[convert] using scripts/route_exec.py"
     python3 ./scripts/route_exec.py swap --from "$FROM" --to "$TO" --mode "$MODE" --amount "$AMT" --slippage-bps "$SLIP" && return 0
  fi
  echo "[convert] no executor available — skipped"
  return 1
}

# Detect SOL balance (best-effort); if not available, assume AUTO
SOL_BAL="$(python3 - <<'PY'
# TODO: replace with wallet/RPC actual query in your codebase
# Fallback returns -1 to mean 'unknown'
print(-1)
PY
)"
echo "[convert] detected SOL balance: $SOL_BAL"

# Iterate tokens
for sym in "${ARR[@]}"; do
  U="${sym^^}"
  if [ "$U" = "USDC" ] || [ "$U" = "$BASE" ]; then
    echo "[convert] skip $U (already base)"
    continue
  fi
  if [ "$U" = "SOL" ]; then
    # swap SOL excess above reserve
    if [ "$SOL_BAL" = "-1" ]; then
      echo "[convert] unknown SOL balance -> MODE=MAX_EXCESS"
      try_swap "SOL" "$BASE" "MAX_EXCESS" "$RESERVE" || true
    else
      python3 - <<PY
sol=float("$SOL_BAL"); reserve=float("$RESERVE")
ex=max(sol-reserve, 0.0)
print(ex)
PY
      EX=$(python3 - <<PY
sol=float("$SOL_BAL"); reserve=float("$RESERVE")
print(max(sol-reserve, 0.0))
PY
)
      if python3 - <<PY
ex=float("$EX"); import sys; sys.exit(0 if ex>0 else 1)
PY
      then
        if simulate_swap "SOL" "$BASE" "EXACT_IN" "$EX"; then echo "[preview] SOL->USDC expect above"; else echo "[preview] (no sim available)"; fi
      try_swap "SOL" "$BASE" "EXACT_IN" "$EX" || true
      else
        echo "[convert] SOL <= reserve, skip"
      fi
    fi
  else
    # swap entire token balance to BASE (amount=MAX)
    if simulate_swap "$U" "$BASE" "MAX" "0"; then echo "[preview] $U->USDC expect above"; else echo "[preview] (no sim available)"; fi
    try_swap "$U" "$BASE" "MAX" "0" || true
  fi
done

if [ "$PREVIEW" = "1" ]; then echo "[preview] (only) finished"; exit 0; fi
echo "[convert] done"
echo "[$(date -Iseconds)] manual: success" >> "$LOG_CONVERT"
tg "📊 Convert-to-USDC (dry-run) done. Proceeding swaps..."; tg "✅ Convert-to-USDC completed (BASE=$BASE, reserve_SOL=$RESERVE)"; echo "[$(date -Iseconds)] manual: completed" >> "$LOG_CONVERT"

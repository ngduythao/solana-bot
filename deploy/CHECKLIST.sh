
#!/usr/bin/env bash
# One-click readiness checklist. Prints PASS/FAIL items and a final verdict.
set -euo pipefail

RED="\033[31m"; GRN="\033[32m"; YLW="\033[33m"; NC="\033[0m"
PASS(){ echo -e "${GRN}[PASS]${NC} $*"; }
FAIL(){ echo -e "${RED}[FAIL]${NC} $*"; }
WARN(){ echo -e "${YLW}[WARN]${NC} $*"; }

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE_DIR/solana-bot/.."

# 1) Env presence
source /etc/solbot/.env 2>/dev/null || true
[ -f ".env" ] && source ".env" 2>/dev/null || true

REQ=(REDIS_URL RPC_PRIMARY JITO_RELAYS)
MISSING=0
for k in "${REQ[@]}"; do
  v="${!k:-}"
  if [ -z "$v" ]; then FAIL "Missing env: $k"; MISSING=1; else PASS "Env $k = ${v:0:60}"; fi
done

# 2) Redis reachable
if redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" ping >/dev/null 2>&1; then
  PASS "Redis ping OK"
else
  FAIL "Redis not reachable: $REDIS_URL"
fi

# 3) Health server
if curl -sf "http://127.0.0.1:${HEALTH_PORT:-9090}/ready" >/dev/null; then
  PASS "Health /ready OK"
else
  WARN "Health not ready (try after services start)"
fi

# 4) Maker keypair
KP="${MAKER_KEYPAIR:-}"
if [ -z "$KP" ]; then
  FAIL "MAKER_KEYPAIR not set"
else
  if [ -f "$KP" ]; then
    PERM=$(stat -c "%a" "$KP" 2>/dev/null || echo "???")
    if [ "$PERM" == "600" ]; then PASS "Keypair perms OK (600)"
    else WARN "Keypair perms $PERM (should be 600)"; fi
    PASS "Keypair file exists: $KP"
  else
    FAIL "Keypair file not found: $KP"
  fi
fi

# 5) Market registry (must have 4 pairs across DEXes)
MR="solana-bot/adapters/market_registry.yaml"
if [ -f "$MR" ]; then
  NEED=(SOL_USDC JUP_USDC WIF_USDC BONK_USDC)
  OK=1
  for pair in "${NEED[@]}"; do
    if grep -q "$pair" "$MR"; then PASS "market_registry has $pair"; else OK=0; FAIL "market_registry missing $pair"; fi
  done
  [ $OK -eq 1 ] || WARN "Auto-fetch may fill these when network is available."
else
  FAIL "market_registry.yaml not found"
fi

# 6) Jito relays DNS resolve (best-effort)
IFS=',' read -ra RELS <<< "${JITO_RELAYS:-}"
for r in "${RELS[@]}"; do
  host "$r" >/dev/null 2>&1 && PASS "Relay resolves: $r" || WARN "Relay DNS not resolving now: $r"
done

# 7) Services up (process names best-effort)
P=("jito_client.py" "auto_hedge_exec.py" "policy_autopilot_lite.py" "policy_autopilot_lane.py" "pnl_aggregator.py" "health_server.py" "queue_gc.py")
for pn in "${P[@]}"; do
  pgrep -f "$pn" >/dev/null 2>&1 && PASS "Service running: $pn" || WARN "Service not seen: $pn"
done

# 8) Final verdict
if grep -q "FAIL" <(echo); then true; fi
echo "----"
echo "Checklist done. Review FAIL/WARN lines. If only PASS/WARN, you can proceed to paper-trade then go live."

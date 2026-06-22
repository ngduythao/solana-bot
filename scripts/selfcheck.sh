#!/usr/bin/env bash
# scripts/selfcheck.sh — preflight checker for non-dev users
set -euo pipefail
LOGDIR="${LOGDIR:-logs}"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/selfcheck.log"
: > "$LOG"

red()  { printf "\033[31m%s\033[0m\n" "$*"; }
yel()  { printf "\033[33m%s\033[0m\n" "$*"; }
grn()  { printf "\033[32m%s\033[0m\n" "$*"; }
info() { echo "$*" | tee -a "$LOG"; }
warn() { yel "$*" | tee -a "$LOG"; }
fail() { red "$*" | tee -a "$LOG"; }

# Load .env if present
if [ -f ".env" ]; then
  set -a; . ./.env; set +a
fi

OK=0; WARN=0; ERR=0

# 1) WALLET_PUBKEY
if [ -n "${WALLET_PUBKEY:-}" ] && [ "${#WALLET_PUBKEY}" -ge 32 ]; then
  info "[WALLET] WALLET_PUBKEY detected: $WALLET_PUBKEY"
  OK=$((OK+1))
else
  warn "[WALLET] WALLET_PUBKEY missing or invalid. Set it in .env"
  WARN=$((WARN+1))
fi

# 2) Key presence (prefer GPG)
if [ -f "/opt/solbot/keys/id.json.gpg" ]; then
  # quick decrypt test (no output)
  if gpg --quiet --batch -d /opt/solbot/keys/id.json.gpg >/dev/null 2>&1; then
    info "[KEY] Found /opt/solbot/keys/id.json.gpg and decryptable via gpg-agent."
    OK=$((OK+1))
  else
    warn "[KEY] /opt/solbot/keys/id.json.gpg present but cannot decrypt (check gpg-agent/passphrase)."
    WARN=$((WARN+1))
  fi
elif [ -f "/root/id.json" ]; then
  warn "[KEY] Found raw /root/id.json (not encrypted). Consider encrypting to /opt/solbot/keys/id.json.gpg"
  OK=$((OK+1))
else
  fail "[KEY] No key found. Provide /opt/solbot/keys/id.json.gpg (recommended) or /root/id.json"
  ERR=$((ERR+1))
fi

# 3) RPC discovery
RPC_ACTIVE="${RPC_URL:-${SOLANA_RPC_URL:-}}"
if [ -z "$RPC_ACTIVE" ] && [ -n "${RPC_CANDIDATES:-}" ]; then
  RPC_ACTIVE="$(echo "$RPC_CANDIDATES" | awk -F, '{print $1}')"
fi

if [ -z "$RPC_ACTIVE" ]; then
  warn "[RPC] No RPC_URL/SOLANA_RPC_URL/RPC_CANDIDATES set in .env — some features may not work."
  WARN=$((WARN+1))
else
  # quick JSON-RPC calls
  if command -v curl >/dev/null 2>&1; then
    H=$(curl -m 3 -sS -X POST -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' "$RPC_ACTIVE" || true)
    if echo "$H" | grep -q '"result":"ok"'; then
      info "[RPC] $RPC_ACTIVE healthy (getHealth=ok)"
      OK=$((OK+1))
    else
      warn "[RPC] $RPC_ACTIVE reachable but not healthy (getHealth)."
      WARN=$((WARN+1))
    fi
  else
    warn "[SYS] curl not found — skip active RPC health probe."
    WARN=$((WARN+1))
  fi
fi

# 4) Redis
if command -v redis-cli >/dev/null 2>&1; then
  if redis-cli ping >/dev/null 2>&1; then
    info "[REDIS] OK (PING)"
    OK=$((OK+1))
  else
    warn "[REDIS] redis-cli present but PING failed. Is redis-server running?"
    WARN=$((WARN+1))
  fi
else
  warn "[REDIS] redis-cli not found. Autorun should have installed Redis — re-run setup if missing."
  WARN=$((WARN+1))
fi

# 5) Panel port conflict (8080)
if ss -ltn '( sport = :8080 )' 2>/dev/null | grep -q 8080; then
  info "[PANEL] Port 8080 is listening."
  OK=$((OK+1))
else
  warn "[PANEL] Port 8080 not listening yet (panel will start shortly)."
  WARN=$((WARN+1))
fi

# 6) Jito optional check
if [ -n "${JITO_RELAYS_CANDIDATES:-}" ]; then
  CNT=$(echo "$JITO_RELAYS_CANDIDATES" | tr ',' '\n' | grep -c . || true)
  info "[JITO] Relays configured: $CNT"
  OK=$((OK+1))
else
  warn "[JITO] No Jito relays configured (optional). Set JITO_RELAYS_CANDIDATES in .env for better latency."
  WARN=$((WARN+1))
fi

echo "OK=$OK WARN=$WARN ERR=$ERR" > .selfcheck_status
if [ "$ERR" -gt 0 ]; then
  yel "=== SELF-CHECK completed with ERRORS (see $LOG). Bot will still launch, but please fix above items. ==="
else
  grn "=== SELF-CHECK OK (OK=$OK, WARN=$WARN). Details: $LOG ==="
fi

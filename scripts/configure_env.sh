#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENV=".env"
[[ -f "$ENV" ]] || cp .env.example "$ENV"

set_kv () {
  key="$1"; val="$2"
  if grep -q "^${key}=" "$ENV"; then
    sed -i "s#^${key}=.*#${key}=${val}#g" "$ENV"
  else
    echo "${key}=${val}" >> "$ENV"
  fi
}

# Inputs (env var or prompt fallback)
HELIUS_RPC_INPUT="${HELIUS_RPC_INPUT:-}"
WALLET_PATH_INPUT="${WALLET_PATH_INPUT:-wallet/keypair.json}"
TELE_BOT="${TELEGRAM_BOT_TOKEN_INPUT:-}"
TELE_CHAT="${TELEGRAM_CHAT_ID_INPUT:-}"

if [[ -z "$HELIUS_RPC_INPUT" ]]; then
  read -rp "Paste your HELIUS_RPC (or RPC URL): " HELIUS_RPC_INPUT
fi

set_kv "HELIUS_RPC" "$HELIUS_RPC_INPUT"
set_kv "RPC_PRIMARY" "$HELIUS_RPC_INPUT"
set_kv "WALLET_PATH" "$WALLET_PATH_INPUT"
if [[ -n "$TELE_BOT" ]]; then set_kv "TELEGRAM_BOT_TOKEN" "$TELE_BOT"; fi
if [[ -n "$TELE_CHAT" ]]; then set_kv "TELEGRAM_CHAT_ID" "$TELE_CHAT"; fi

echo "Updated .env"

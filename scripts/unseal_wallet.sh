#!/usr/bin/env bash
set -euo pipefail
: "${WALLET_GPG_PATH:=wallet/keypair.json.gpg}"
: "${WALLET_TMPFS_PATH:=/dev/shm/solbot_keypair.json}"
: "${WALLET_PASSPHRASE:=}"

if [[ ! -f "$WALLET_GPG_PATH" ]]; then
  echo "[unseal] WARNING: $WALLET_GPG_PATH not found; fallback to plaintext key if exists."
  exit 0
fi

mkdir -p "$(dirname "$WALLET_TMPFS_PATH")"
if [[ -n "$WALLET_PASSPHRASE" ]]; then
  echo "$WALLET_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 -o "$WALLET_TMPFS_PATH" -d "$WALLET_GPG_PATH"
else
  gpg --batch --yes -o "$WALLET_TMPFS_PATH" -d "$WALLET_GPG_PATH"
fi
chmod 600 "$WALLET_TMPFS_PATH"
echo "[unseal] wallet to $WALLET_TMPFS_PATH"

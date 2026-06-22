#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[prefill] autodiscover pools for SOL,JUP,BONK,WIF vs USDC"
docker compose run --rm autodiscover || true
if [[ -f config/pools.yaml ]]; then
  cp config/pools.yaml config/pools.lock.yaml
  echo "[prefill] pools locked -> config/pools.lock.yaml"
fi
echo "[prefill] done."

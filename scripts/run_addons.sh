#!/usr/bin/env bash
set -euo pipefail

if command -v docker compose >/dev/null; then
  DC="docker compose"
else
  DC="docker compose"
fi

# Bring up core stack
$DC up -d

# Bring up optional addon services when enabled in config.yaml.
if grep -q '^\s*enable_funding:\s*true' config.yaml; then
  echo "[ADDONS] Enabling funding module..."
  $DC -f docker-compose.yml -f docker-compose.addons.yml up -d funding
fi

if grep -q '^\s*enable_liquidation:\s*true' config.yaml; then
  echo "[ADDONS] Enabling liquidation module..."
  $DC -f docker-compose.yml -f docker-compose.addons.yml up -d liquidation
fi

echo "Addon services started when enabled. Dashboard on port 8081."

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Validate docker & compose
docker compose version >/dev/null

# Use production env if present
if [ -f .env.production ]; then
  cp .env.production .env
elif [ -f .env.production.example ] && [ ! -f .env ]; then
  cp .env.production.example .env
fi

# Validate compose and bring-up using build override for pinned images
docker compose -f docker-compose.yml -f docker-compose.build.yml build
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d

# Wait for health
./scripts/smoke_health.sh

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Ensure docker & compose
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  echo "[ONECLICK] Docker missing; running fix..."
  sudo ./fix_docker_ubuntu24.sh
fi

# Use existing .env or create from example
[ -f .env ] || cp .env.example .env

./check_compose.sh
docker compose up -d redis dashboard metrics-exporter
sleep 3
docker compose ps
docker compose logs --tail=120 dashboard || true

docker compose up -d orchestrator ops-guard signer prometheus grafana cex-orchestrator hedger
echo "[ONECLICK] Up. Dashboard: http://<IP>:8080"

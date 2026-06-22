#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "=== DIAG: tools ==="; docker --version || true; docker compose version || { echo "[ERR] compose v2 missing"; exit 1; }
echo "=== DIAG: ensure dirs ==="; mkdir -p dashboard tuner analytics certs prometheus grafana secrets orchestrator guard metrics_exporter; touch config.yaml
echo "=== DIAG: compose config ==="; docker compose -f docker-compose.yml config || true
echo "=== DIAG: run minimal ==="; docker compose up -d redis dashboard metrics-exporter || true; docker compose ps
echo "=== DIAG: dashboard logs ==="; docker compose logs --tail=120 dashboard || true

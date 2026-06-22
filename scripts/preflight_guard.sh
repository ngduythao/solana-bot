#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/solanabot"
[ -f "./docker-compose.yml" ] && ROOT="$(pwd)"
cd "$ROOT"
echo "[preflight] Checking secrets & env..."
if [ ! -f .env ]; then echo "[warn] .env chưa có, sẽ dùng .env.example -> .env"; cp -n .env.example .env || true; fi
echo "[SMOKE] Checking prerequisites..."
command -v docker >/dev/null || { echo "[ERR] Docker chưa cài"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[ERR] docker compose v2 thiếu"; exit 1; }
echo "[SMOKE] Checking .env... done"
./check_compose.sh
./diag.sh

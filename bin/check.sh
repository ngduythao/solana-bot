#!/usr/bin/env bash
set -euo pipefail
if ! command -v docker >/dev/null; then echo "[ERR] docker not found"; exit 1; fi
if ! docker compose version >/dev/null 2>&1; then echo "[ERR] docker compose v2 not found. Try: sudo apt install -y docker-compose-plugin"; exit 1; fi
if [ ! -f ".env" ]; then echo "[ERR] .env missing. cp .env.example .env"; exit 1; fi
if [ ! -f "docker-compose.yml" ]; then echo "[ERR] docker-compose.yml missing"; exit 1; fi
echo "[OK] Environment check passed."

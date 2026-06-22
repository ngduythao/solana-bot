#!/usr/bin/env bash
set -euo pipefail
if [ ! -f .env ]; then cp .env.example .env; fi
if ! command -v docker &>/dev/null; then echo "❌ Docker chưa cài. Cài Docker rồi chạy lại."; exit 1; fi
if ! command -v docker compose &>/dev/null; then echo "❌ Docker Compose chưa sẵn."; exit 1; fi
chmod +x run.sh
./run.sh up
./run.sh logs

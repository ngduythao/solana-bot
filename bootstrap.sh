#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Fix Docker on Ubuntu 24.04 if needed
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  echo "[BOOTSTRAP] Installing/fixing Docker..."
  sudo ./fix_docker_ubuntu24.sh
fi

# Prepare env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[BOOTSTRAP] Created .env from example. Edit it now to set RPC/Jito/keys if needed."
fi

# Validate compose
./check_compose.sh

# Ensure dirs then bring up full stack
make dirs
make run-all

echo "[BOOTSTRAP] Done. Dashboard: http://<IP>:8080  Grafana: http://<IP>:3001  Prometheus: http://<IP>:9090"

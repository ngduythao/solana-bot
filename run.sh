#!/usr/bin/env bash
set -euo pipefail
source .env || true
python3 scripts/check_env.py || true
./bootstrap.sh || docker compose up -d
echo "Solbot31 is up. Visit Dashboard at http://localhost:8080"

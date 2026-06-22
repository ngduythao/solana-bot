#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/solanabot"
[ -f "./docker-compose.yml" ] && ROOT="$(pwd)"
cd "$ROOT"
./scripts/prod_up.sh

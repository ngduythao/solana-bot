#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [ -x "./scripts/net_benchmark.sh" ]; then
  ./scripts/net_benchmark.sh
else
  echo "net_benchmark.sh not found"
fi

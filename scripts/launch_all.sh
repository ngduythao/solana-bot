#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate || true
find "$ROOT/scripts" -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; -exec chmod +x {} \; 2>/dev/null || true

# Do NOT auto-start engine; default paused
mkdir -p /opt/solbot/state
echo "1" > /opt/solbot/state/paused || true

# Start combined panel
./scripts/serve_dashboard.sh || true

# Watchdog for combined panel
while true; do
  curl -sS http://127.0.0.1:8080/api/health >/dev/null || (echo "[watchdog] restarting panel..." && ./scripts/serve_dashboard.sh || true)
  sleep 30
done

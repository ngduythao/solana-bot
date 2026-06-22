#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[SMOKE] docker ps:"
docker compose ps

echo "[SMOKE] waiting for dashboard (max 60s)..."
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8080/ >/dev/null 2>&1; then
    echo "[OK] dashboard ready"; break
  fi
  sleep 2
done

echo "[SMOKE] metrics:"
curl -fsS http://127.0.0.1:9100/ >/dev/null && echo "[OK] metrics-exporter ok" || echo "[WARN] metrics-exporter not ready"

echo "[SMOKE] prometheus:"
curl -fsS http://127.0.0.1:9090/-/ready >/dev/null && echo "[OK] prometheus ok" || echo "[WARN] prometheus not ready"

echo "[SMOKE] grafana:"
curl -fsS http://127.0.0.1:3001/login >/dev/null && echo "[OK] grafana ok" || echo "[WARN] grafana not ready"

exit 0

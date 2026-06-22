#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/solanabot"
[ -f "./docker-compose.yml" ] && ROOT="$(pwd)"
cd "$ROOT"
echo "[SMOKE] Starting minimal stack (redis + dashboard + metrics-exporter)..."
docker compose up -d redis dashboard metrics-exporter
sleep 3
docker compose ps
docker compose logs --tail=120 dashboard || true
python - <<'PY'
import urllib.request,sys
try:
    urllib.request.urlopen("http://127.0.0.1:8080/",timeout=3)
    print("[OK] dashboard up")
except Exception as e:
    print("[WARN] dashboard not responding:",e)
PY

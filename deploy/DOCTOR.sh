
#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$BASE_DIR/solana-bot"
cd "$APP_DIR"
echo "[DOCTOR] Python: $(python3 -V)"
echo "[DOCTOR] Venv: ${VIRTUAL_ENV:-none}"
if [ ! -d ".venv" ]; then
  echo "[DOCTOR] Creating venv..."; python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip >/dev/null
REQ="requirements_min.txt"; [ -f requirements.txt ] && REQ="requirements.txt"
pip install -r "$REQ" >/dev/null || true
echo "[DOCTOR] Redis ping:"; redis-cli ping || true
echo "[DOCTOR] Ports:"; ss -ltn '( sport = :8080 or sport = :8081 )' || true
echo "[DOCTOR] Env snapshot:"; python - <<'PY'
import os, json; keys=['RPC_PRIMARY','REDIS_URL','JITO_RELAYS']; print(json.dumps({k:os.getenv(k) for k in keys}, indent=2))
PY
echo "[DOCTOR] Recent warnings:"; redis-cli lrange solbot:warnings 0 10 || true
echo "[DOCTOR] Done."

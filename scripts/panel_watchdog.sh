#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ensure venv and deps
[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate
python3 - <<'PY' || true
import importlib, subprocess, sys
for p in ["fastapi","uvicorn","pydantic","starlette","aiofiles","httpx"]:
    try: importlib.import_module(p)
    except Exception: subprocess.run([sys.executable,"-m","pip","install","-q","--upgrade",p], check=False)
PY

attempt=0
max_attempts=5
while (( attempt < max_attempts )); do
  attempt=$((attempt+1))
  # health probe
  if curl -sS http://127.0.0.1:8080/api/health | grep -q '"ok": *true'; then
    echo "[watchdog] Panel healthy on 127.0.0.1:8080"
    exit 0
  fi
  echo "[watchdog] Panel not healthy (attempt $attempt) -> repairing..."

  # free port 8080 if stuck
  pids=$(ss -ltnp | awk '/127.0.0.1:8080/ {print $7}' | sed -E 's/users:\(\("([^"]+)",pid=([0-9]+).*/\2/')
  if [ -n "${pids:-}" ]; then
    echo "[watchdog] Killing PID(s) on 8080: $pids"
    for pid in $pids; do kill -9 "$pid" 2>/dev/null || true; done
  fi

  # restart tmux panel session
  tmux kill-session -t solbot_panel 2>/dev/null || true
  tmux new-session -d -s solbot_panel "bash -lc 'source .venv/bin/activate; export PYTHONPATH=$PWD; exec python3 -m analytics.panel_latency_pnl 2>&1 | tee -a /tmp/solbot_panel.log'"
  sleep 2
done

echo "[watchdog] Panel still not healthy. Last 80 lines:"
tail -n 80 /tmp/solbot_panel.log 2>/dev/null || true
exit 1

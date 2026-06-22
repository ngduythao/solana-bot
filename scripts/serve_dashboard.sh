#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate
export PYTHONPATH="$PWD"
python3 - <<'PY' || true
import importlib, subprocess, sys
for p in ["fastapi","uvicorn","pydantic","starlette","aiofiles","httpx"]:
    try: importlib.import_module(p)
    except Exception: subprocess.run([sys.executable,"-m","pip","install","-q","--upgrade",p], check=False)
PY
# start legacy panel on 8081
tmux kill-session -t solbot_panel_inner 2>/dev/null || true
tmux new-session -d -s solbot_panel_inner "bash -lc 'source .venv/bin/activate; export PYTHONPATH=$PWD; exec python3 -m analytics.panel_latency_pnl --host 127.0.0.1 --port 8081 2>&1 | tee -a /tmp/solbot_panel_inner.log'"
# start combined panel on 8080
tmux kill-session -t solbot_panel 2>/dev/null || true
tmux new-session -d -s solbot_panel "bash -lc 'source .venv/bin/activate; export PYTHONPATH=$PWD; exec uvicorn analytics.panel_combined:app --host 127.0.0.1 --port 8080 2>&1 | tee -a /tmp/solbot_panel.log'"
echo "[✓] Combined panel on 127.0.0.1:8080 (includes control); inner panel on 127.0.0.1:8081"

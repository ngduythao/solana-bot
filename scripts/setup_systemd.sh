#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT_DIR/.venv/bin/activate"

create_unit () {
  local name="$1"; local workdir="$2"; local cmd="$3"
  local unit="/etc/systemd/system/${name}.service"
  sudo bash -c "cat > $unit" <<EOF
[Unit]
Description=$name
After=network.target redis-server.service

[Service]
Type=simple
WorkingDirectory=$workdir
EnvironmentFile=$ROOT_DIR/.env
ExecStart=/bin/bash -lc 'source $VENV && $cmd'
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
  sudo systemctl daemon-reload
  sudo systemctl enable "$name"
  sudo systemctl restart "$name"
  echo "[+] Installed $unit"
}

[ -f backrun/backrun.py ] && create_unit "solbot-backrun" "$ROOT_DIR/backrun" "python3 backrun.py"
[ -f rpc_router/ws_listener.py ] && create_unit "solbot-ws" "$ROOT_DIR/rpc_router" "python3 ws_listener.py"
[ -f jito_submitter/submitter.py ] && create_unit "solbot-jito" "$ROOT_DIR/jito_submitter" "python3 submitter.py"
[ -f alerts_runner/alerts.py ] && create_unit "solbot-alerts" "$ROOT_DIR/alerts_runner" "python3 alerts.py"

echo "[+] Systemd services installed."


[ -f services/hedge_policy.py ] && create_unit "solbot-hedge-policy" "$ROOT_DIR/services" "python3 hedge_policy.py"

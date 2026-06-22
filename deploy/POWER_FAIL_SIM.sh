
#!/usr/bin/env bash
set -euo pipefail
echo "[SIM] Emulating sudden power loss (stop services abruptly)"
sudo systemctl stop solbot_fast@${USER} solbot_boot@${USER} solbot_planexec@${USER} || true
sudo pkill -9 -f solana-bot || true
echo "[SIM] Sleeping 3s (power off)"; sleep 3
echo "[SIM] Power back — starting boot watchdog"
sudo systemctl start solbot_boot@${USER} || true
sleep 2
systemctl status solbot_boot@${USER} --no-pager -l | sed -n '1,80p'

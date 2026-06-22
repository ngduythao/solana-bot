#!/usr/bin/env bash
# Ping panel health; if down, restart the unified service.
set -euo pipefail
LOGFILE=/var/log/solbot_cron.log
TS() { date '+%Y-%m-%d %H:%M:%S'; }
echo "$(TS) [cron] healthcheck start" >> "$LOGFILE"
if curl -sS --max-time 5 http://127.0.0.1:8080/api/health | grep -q '"ok": *true'; then
  echo "$(TS) [cron] panel OK" >> "$LOGFILE"
  exit 0
else
  echo "$(TS) [cron] panel FAIL -> restarting service" >> "$LOGFILE"
  /bin/systemctl restart solbot-all.service || echo "$(TS) [cron] restart failed" >> "$LOGFILE"
fi

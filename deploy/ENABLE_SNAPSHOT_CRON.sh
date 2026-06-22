
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
( crontab -l 2>/dev/null; echo "0 3 * * * bash $(cd $(dirname $0) && pwd)/SNAPSHOT_EXPORT.sh >/var/log/solbot_snapshot.log 2>&1" ) | crontab -
echo "[CRON] Nightly snapshot at 03:00 configured."

#!/usr/bin/env bash
# RATE_LIMIT
#!/usr/bin/env bash
# Safe Telegram notifier with alerts toggle
set +x
set -euo pipefail
TOKEN="${TELEGRAM_BOT_TOKEN:-}"
IDS="${TELEGRAM_CHAT_IDS:-}"
MSG="${1:-}"
STATE_FILE="/opt/solbot/state/alerts_enabled"
# default enabled if file absent
ALERTS_ENABLED="1"
if [ -f "$STATE_FILE" ]; then
  ALERTS_ENABLED="$(cat "$STATE_FILE" 2>/dev/null || echo 1)"
fi
[ "$ALERTS_ENABLED" = "1" ] || exit 0
[ -z "$TOKEN" ] && exit 0
[ -z "$IDS" ] && exit 0
for id in ${IDS//,/ } ; do
  redis-cli setex last_tg_msg:$(echo "$1"|md5sum|cut -d' ' -f1) 300 1 || true
if redis-cli get last_tg_msg:$(echo "$1"|md5sum|cut -d' ' -f1)>/dev/null; then exit 0; fi
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" -d "chat_id=${id}" -d "text=${MSG}" >/dev/null 2>&1 || true
done


#!/usr/bin/env bash
set -euo pipefail
: "${TELEGRAM_BOT_TOKEN:?Set TELEGRAM_BOT_TOKEN in env}"
: "${TELEGRAM_CHAT_ID:?Set TELEGRAM_CHAT_ID in env}"
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"   -d chat_id="${TELEGRAM_CHAT_ID}" -d text="Solbot telegram test: $(date -Iseconds)" -d disable_notification=true
echo ""

#!/usr/bin/env bash
# Send daily PnL summary to Telegram at configured hour (VN time). Best-effort reads Redis keys.
set -euo pipefail
cd "$(dirname "$0")/.."

# helper
tg(){ ./scripts/tg_notify.sh "$1" >/dev/null 2>&1 || true; }

# Read stats from Redis (best-effort)
REDIS_PNL=$(redis-cli GET hsbot:pnl:daily_usd 2>/dev/null || echo "0")
REDIS_WR=$(redis-cli GET hsbot:winrate_daily 2>/dev/null || echo "0")
LAT50=$(redis-cli GET hsbot:lat_p50 2>/dev/null || echo "0")
LAT95=$(redis-cli GET hsbot:lat_p95 2>/dev/null || echo "0")
TRADES=$(redis-cli GET hsbot:trades_daily 2>/dev/null || echo "0")

MSG="📊 Daily Summary (VN)
PNL: ${REDIS_PNL} USDC
Winrate: ${REDIS_WR}%
Trades: ${TRADES}
Latency p50/p95: ${LAT50}/${LAT95} ms"

tg "$MSG"
echo "[$(date -Iseconds)] daily-summary sent: $MSG" >> /var/log/solbot_convert.log

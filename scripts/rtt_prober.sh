#!/usr/bin/env bash
set -euo pipefail
OUT_SUM=/tmp/solbot_rtt_summary.txt
OUT_TAB=/tmp/solbot_rtt_table.txt
RPCS="${RPC_ENDPOINT:-https://api.mainnet-beta.solana.com}"
RELAYS="${JITO_RELAYS:-https://ny.mainnet.block-engine.jito.wtf,https://va.mainnet.block-engine.jito.wtf}"
probe() {
  url="$1"
  t=$(curl -s -o /dev/null -w '%{time_connect};%{time_starttransfer};%{time_total}' --max-time 3 "$url" || echo "0;0;0")
  echo "$url,$t"
}
{
  echo "Target,connect_s,start_s,total_s"
  IFS=','
  for r in $RPCS; do probe "$r"; done
  for j in $RELAYS; do probe "$j/health"; done
} | tee >(awk -F, 'NR>1{c+=$2;s+=$3;t+=$4;n++}END{if(n)printf("avg_total=%.0fms", (t/n)*1000); else print "n/a"}' > "$OUT_SUM") > "$OUT_TAB"


# Optional threshold to alert via Telegram if avg latency too high
THRESH_LAT_MS="${THRESH_LAT_MS:-0}"   # 0 = disabled
OUT_SUM=/tmp/solbot_rtt_summary.txt
OUT_TAB=/tmp/solbot_rtt_table.txt

alert_if_needed() {
  [ -z "$THRESH_LAT_MS" ] && return 0
  [ "$THRESH_LAT_MS" = "0" ] && return 0
  ms=$(awk -F'[= ]+' '/avg_total=/{print $2}' "$OUT_SUM" 2>/dev/null || echo 0)
  if [ -n "$ms" ] && [ "$ms" -gt "$THRESH_LAT_MS" ]; then
    ./scripts/tg_notify.sh "⚠️ RTT avg_total=${ms}ms > ${THRESH_LAT_MS}ms"
  fi
}

# If run with --now, run a one-shot probe & print paths
if [ "${1:-}" = "--now" ]; then
  /bin/bash "$0" || true
  alert_if_needed || true
  echo "$OUT_SUM"
  echo "$OUT_TAB"
  exit 0
fi


# Append history for later stats
HIST="/tmp/solbot_rtt_history.csv"
if [ -f "$OUT_TAB" ]; then
  ts="$(date +%s)"
  awk -v ts="$ts" 'NR>1{print ts","$0}' "$OUT_TAB" >> "$HIST" 2>/dev/null || true
fi

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs/archive

rotate_file(){
  local f="$1"
  [ -f "$f" ] || return 0
  local day=$(date -u -d '+7 hours' +"%Y-%m-%d" 2>/dev/null || date +"%Y-%m-%d")
  local base=$(basename "$f")
  local dest="logs/archive/${day}_${base}"
  cp -f "$f" "$dest" || true
  : > "$f" || true
  gzip -f "$dest" || true
}

prune_old(){
  # keep 7 days
  find logs/archive -type f -name "*.gz" -mtime +7 -delete || true
}

while true; do
  # rotate at 00:05 VN daily
  now=$(date +%s)
  # compute next 00:05 VN epoch via python for reliability
  nxt=$(python3 - <<'PY'
import datetime as dt
now_utc=dt.datetime.utcnow()
vn=now_utc+dt.timedelta(hours=7)
target=vn.replace(hour=0,minute=5,second=0,microsecond=0)
if vn>=target:
    target=target+dt.timedelta(days=1)
target_utc=target-dt.timedelta(hours=7)
print(int(target_utc.timestamp()))
PY
)
  sleep_sec=$(( nxt - now ))
  [ $sleep_sec -gt 0 ] && sleep $sleep_sec
  rotate_file "logs/pnl_by_route.csv"
  rotate_file "logs/pnl_day_timeseries.csv"
  prune_old
  sleep 60
done

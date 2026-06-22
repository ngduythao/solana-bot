#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs/archive

next_epoch_for_vn_midnight() {
  # compute next 00:00 VN (UTC+7)
  python3 - "$@" <<'PY'
import datetime as dt, time
now_utc=dt.datetime.utcnow()
vn=now_utc+dt.timedelta(hours=7)
target=vn.replace(hour=0,minute=0,second=0,microsecond=0)
if vn>=target:
    target=target+dt.timedelta(days=1)
target_utc=target-dt.timedelta(hours=7)
print(int(target_utc.timestamp()))
PY
}

rotate_once() {
  stamp=$(date -u +"%Y-%m-%d_%H-%M-%S")
  day=$(date -u -d '+7 hours' +"%Y-%m-%d") || day=$(date +"%Y-%m-%d")
  dest="logs/archive/$day"
  mkdir -p "$dest"
  shopt -s nullglob
  for f in logs/*.log; do
    base=$(basename "$f")
    cp -f "$f" "$dest/${base%.*}_$stamp.log" || true
    : > "$f" || true
  done
  # gzip old
  find "logs/archive" -type f -name "*.log" -mtime +0 -exec gzip -f {} \; || true
}

while true; do
  now=$(date +%s)
  nxt=$(next_epoch_for_vn_midnight)
  sleep_sec=$(( nxt - now + 60 )) # rotate at 00:01 VN
  if [ $sleep_sec -gt 0 ]; then sleep $sleep_sec; fi
  rotate_once
done

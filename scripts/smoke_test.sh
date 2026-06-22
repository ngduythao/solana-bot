#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

retries=12
ok=0
for i in $(seq 1 $retries); do
  sleep 5
  if curl -fsS http://127.0.0.1:8080/ >/dev/null 2>&1 && \
     curl -fsS http://127.0.0.1:8080/analytics/pnl_status >/dev/null 2>&1 && \
     curl -fsS http://127.0.0.1:8080/guard/check >/dev/null 2>&1 ; then
     ok=1; break
  fi
  echo "[smoke] attempt $i/$retries waiting panel..."
done

if [ "$ok" -eq 1 ]; then
  echo "[smoke] panel healthy"
else
  echo "[smoke] panel not ready after $retries tries" >&2
  exit 1
fi

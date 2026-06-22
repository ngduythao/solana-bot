#!/usr/bin/env bash
# Set per-route capital caps (fraction of notional), e.g. 0.25 = 25%%
set -euo pipefail
PAIR="${1:-}"
CAP="${2:-}"
if [ -z "$PAIR" ] || [ -z "$CAP" ]; then
  echo "Usage: $0 <PAIR> <CAP_FRACTION>"; exit 1
fi
redis-cli SET "hsbot:cap:${PAIR}" "$CAP"
echo "[cap] set ${PAIR} -> ${CAP}"

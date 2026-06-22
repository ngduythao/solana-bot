#!/usr/bin/env bash
# Return 0 if allowed to send (consume one token), 1 otherwise.
set -euo pipefail
TOK=$(redis-cli GET hsbot:pacer:tokens 2>/dev/null || echo "0")
awk -v t="$TOK" 'BEGIN{ if (t+0.0 >= 1.0) { print "ok"; exit 0 } else { exit 1 } }' >/dev/null || exit 1
redis-cli DECRBYFLOAT hsbot:pacer:tokens 1 >/dev/null 2>&1 || true
exit 0


#!/usr/bin/env bash
set -euo pipefail
redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" SETEX solbot:jup:armed "${1:-600}" 1
echo "[ARM] Jupiter HOT swaps armed for ${1:-600}s"

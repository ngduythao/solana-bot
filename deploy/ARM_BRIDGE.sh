
#!/usr/bin/env bash
set -euo pipefail
redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" SETEX solbot:bridge:armed "${1:-900}" 1
echo "[ARM] Bridge armed for ${1:-900}s"


#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$BASE_DIR/strategy/strategy.yaml"
echo "[EMERGENCY] Setting throttle=0.3 for 15m"
redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" SETEX solbot:throttle:factor 900 "0.3"
# Disable surprise-burst
sed -i 's/enable: true/enable: false/' "$CFG" || true
# Optional: enable shadow mode (paper)
if [[ "${FORCE_SHADOW:-0}" == "1" ]]; then
  sed -i 's/shadow_mode:\n  enable: false/shadow_mode:\n  enable: true/' "$CFG" || true
  echo "[EMERGENCY] Shadow mode ON"
fi
echo "[EMERGENCY] Applied conservative mode."

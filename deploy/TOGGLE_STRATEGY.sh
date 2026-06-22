
#!/usr/bin/env bash
set -euo pipefail
mode="${1:-status}"
CFG="$(cd "$(dirname "$0")/.." && pwd)/strategy/strategy.yaml"

case "$mode" in
  stealth-on)
    sed -i 's/private_bundle_only: .*/private_bundle_only: true/' "$CFG"
    echo "[toggle] stealth ON"
    ;;
  stealth-off)
    sed -i 's/private_bundle_only: .*/private_bundle_only: false/' "$CFG"
    echo "[toggle] stealth OFF (not recommended)"
    ;;
  shadow-on)
    sed -i 's/enable: false # paper/enable: true # paper/' "$CFG" 2>/dev/null || true
    sed -i 's/shadow_mode:\n  enable: false/shadow_mode:\n  enable: true/' "$CFG"
    echo "[toggle] shadow mode ON (paper-trade)"
    ;;
  shadow-off)
    sed -i 's/shadow_mode:\n  enable: true/shadow_mode:\n  enable: false/' "$CFG"
    echo "[toggle] shadow mode OFF"
    ;;
  status|*)
    echo "[toggle] showing head of strategy.yaml"; head -n 40 "$CFG"
    ;;
esac

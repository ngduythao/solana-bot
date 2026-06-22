#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail

if command -v docker compose >/dev/null; then
  DC="docker compose"
else
  DC="docker compose"
fi

$DC -f docker compose.yml -f docker compose.hybrid.yml up -d control
echo "✅ One-click up: core + funding + liquidation + orchestrator + dex-dispatcher + cex-exec + hedge-exec + backrun-ws + ai-fee. Dashboard on port 8081."

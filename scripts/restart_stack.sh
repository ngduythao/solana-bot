#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
PROFILE="${1:?Usage: $0 <profile> }"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[*] Restarting solbot with profile: $PROFILE"
# Kill known tmux sessions
for s in solbot_route_penalty solbot-prober solbot-jito-autotune solbot-scorer solbot-hedger solbot-hedge-policy; do
  tmux kill-session -t "$s" 2>/dev/null || true
done

# Optionally stop systemd services if used (best-effort)
for svc in solbot-prober solbot-jito-autotune solbot-scorer solbot-hedger solbot-hedge-policy; do
  systemctl stop "$svc" 2>/dev/null || true
done

# Relaunch via oneclick
exec ./scripts/oneclick.sh "$PROFILE"

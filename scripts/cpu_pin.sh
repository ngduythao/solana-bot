#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
# Pin critical processes to selected CPU cores.
# Usage:
#   CPU_PIN="2-5" ./scripts/cpu_pin.sh
#   CPU_PIN="0,2,4" ./scripts/cpu_pin.sh
#
# By default, targets include jito submitter/executor/confirm watchers.
CPU_PIN="${CPU_PIN:-}"
if [ -z "$CPU_PIN" ]; then
  echo "[!] Set CPU_PIN (e.g., '2-5' or '0,2,4')."; exit 0
fi
if ! command -v taskset >/dev/null; then
  echo "[!] taskset not found (apt install util-linux)."; exit 0
fi

# pgrep patterns (adjust as needed)
PATTERNS=(
  "jito" 
  "submitter"
  "order_executor"
  "confirm_watcher"
  "hedger"
  "hedge_policy"
  "scorer"
  "prober"
)

echo "[*] Pinning PIDs to CPUs: $CPU_PIN"
for pat in "${PATTERNS[@]}"; do
  for pid in $(pgrep -f "$pat" || true); do
    echo "  - taskset -cp $CPU_PIN $pid"
    taskset -cp "$CPU_PIN" "$pid" >/dev/null || true
  done
done
echo "[✓] CPU pin applied."

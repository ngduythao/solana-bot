
#!/usr/bin/env bash
# Run critical services with CPU affinity + high priority (chrt -f).
# Usage: sudo bash deploy/RUN_FAST.sh
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$BASE_DIR/.venv/bin/python"

# pick isolated CPUs if available, else CPU0-1
CPUS="${CPUS:-0-1}"
PRIO="${PRIO:-70}"

function runp() {
  local name="$1"; shift
  echo "[FAST] start $name (cpus=$CPUS prio=$PRIO)"
  taskset -c "$CPUS" chrt -f "$PRIO" "$@"
}

cd "$BASE_DIR"
runp fast_executor $VENV services/fast_executor.py &
# Pin jito_client/policy services as well if present
pgrep -f jito_client.py >/dev/null && echo "[FAST] jito_client already running" || runp jito_client $VENV services/jito_client.py &
pgrep -f policy_autopilot_lane.py >/dev/null && echo "[FAST] autopilot_lane already running" || runp autopilot_lane $VENV services/policy_autopilot_lane.py &
wait

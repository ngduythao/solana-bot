
#!/usr/bin/env bash
set -euo pipefail
echo "[PREFLIGHT] Checking environment & prerequisites"
bash "$(dirname "$0")/VALIDATE_ENV.sh" || { echo "Fix .env first"; exit 2; }
command -v redis-cli >/dev/null || { echo "Missing redis-cli"; exit 2; }
echo "[PREFLIGHT] OK"

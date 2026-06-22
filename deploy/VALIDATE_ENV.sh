
#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="/etc/solbot/.env"
echo "[VALIDATE] Checking $ENV_FILE"
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found"; exit 1; }
source "$ENV_FILE"

ok=1
check_var(){ local n="$1"; eval "v=\${$n:-}"; if [[ -z "${v:-}" ]]; then echo "MISSING: $n"; ok=0; fi; }
# Required for HOT mode
if [[ "${SIGNER_MODE:-paper}" == "hot" ]]; then
  check_var KEYPAIR_PATH
  check_var RPC_URL
  if ! command -v solana >/dev/null 2>&1; then echo "MISSING: solana CLI (run INSTALL_SOLANA_CLI.sh)"; ok=0; fi
fi

# Safety bounds
: "${JUP_MAX_SLIPPAGE_BPS:=80}"
if (( JUP_MAX_SLIPPAGE_BPS <= 0 || JUP_MAX_SLIPPAGE_BPS > 500 )); then echo "WARN: JUP_MAX_SLIPPAGE_BPS unusual ($JUP_MAX_SLIPPAGE_BPS)"; fi

if (( ok==0 )); then echo "[VALIDATE] FAILED"; exit 2; fi
echo "[VALIDATE] OK"

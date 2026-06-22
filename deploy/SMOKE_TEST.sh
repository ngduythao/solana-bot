
#!/usr/bin/env bash
set -euo pipefail
echo "[SMOKE] Redis:"; redis-cli ping || (echo "Redis FAIL" && exit 1)
echo "[SMOKE] RPC_PRIMARY:"; python3 - <<'PY'
import os,requests,json; import sys
url=os.getenv('RPC_PRIMARY','https://api.mainnet-beta.solana.com')
try:
  r=requests.post(url,json={'jsonrpc':'2.0','id':1,'method':'getHealth'})
  print('[SMOKE] RPC status', r.status_code)
except Exception as e:
  print('RPC FAIL', e); sys.exit(1)
PY
echo "[SMOKE] WS service health:"; curl -sf http://127.0.0.1:9090/live || (echo "Health FAIL" && exit 1)
echo "[SMOKE] OK"

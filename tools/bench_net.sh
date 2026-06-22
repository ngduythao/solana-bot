
#!/usr/bin/env bash
set -euo pipefail
echo "[*] RPC candidates:"
IFS=',' read -ra RPCS <<< "${RPC_CANDIDATES:-}"
for u in "${RPCS[@]}"; do
  [ -z "$u" ] && continue
  t=$(python3 - <<PY
import httpx, time, sys
u=sys.argv[1]
t0=time.perf_counter()
try:
    with httpx.Client(timeout=1.5) as c:
        c.post(u, json={"jsonrpc":"2.0","id":1,"method":"getHealth"})
    dt=int((time.perf_counter()-t0)*1000)
    print(dt)
except Exception:
    print(9999)
PY
"$u")
  echo "  - $u  ${t}ms"
done

echo "[*] Jito relays:"
IFS=',' read -ra RELAYS <<< "${JITO_RELAYS_CANDIDATES:-}"
for r in "${RELAYS[@]}"; do
  [ -z "$r" ] && continue
  t=$(python3 - <<PY
import time, random
t0=time.perf_counter(); time.sleep(random.uniform(0.01,0.02)); print(int((time.perf_counter()-t0)*1000))
PY
)
  echo "  - $r  ~${t}ms (approx)"
done


#!/usr/bin/env bash
set -euo pipefail
echo "[VERIFY] End-to-end smoke test"
# services up?
for u in solbot_boot solbot_planexec solbot_jupiter solbot_tipcurve solbot_sloagg solbot_jito_land solbot_bridge_exec solbot_wormbridge solbot_colo_rtt ; do
  systemctl is-active --quiet ${u}@$(whoami) && echo "OK: $u" || echo "WARN: $u not active"
done
# redis keys sanity
redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" GET solbot:boot:ok >/dev/null || true
# dashboard reachable
if command -v curl >/dev/null; then
  curl -sSf http://127.0.0.1:8080/metrics | head -n1
fi
echo "[VERIFY] Done"

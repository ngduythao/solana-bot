
#!/usr/bin/env bash
set -e
echo "[HEALTH] Checking ports 8080/8081 ..."
ss -ltn '( sport = :8080 or sport = :8081 )' || true
echo "[HEALTH] Redis ping:"
redis-cli ping || true
echo "[HEALTH] Env:"
python3 -c "import os;print('RPC_PRIMARY=',os.getenv('RPC_PRIMARY','(unset)'))"

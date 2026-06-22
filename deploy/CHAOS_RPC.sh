
#!/usr/bin/env bash
echo "[CHAOS] Simulating RPC kill (replace RPC_URL invalid)"
sed -i 's#^RPC_URL=.*#RPC_URL=http://127.0.0.1:0#' /etc/solbot/.env

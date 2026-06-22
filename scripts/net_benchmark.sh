#!/usr/bin/env bash
set -euo pipefail
echo "== NIC offload features (ethtool) =="
which ethtool >/dev/null 2>&1 && ethtool -k $(ip -o -4 route show to default | awk '{print $5}') || echo "ethtool not installed"
echo "== Current MTU =="
ip link | awk -F'[: ]+' '/mtu/{print $2,$(NF-2),$NF}' | sed 's/^/  /'
echo "== Ping RPC & Jito =="
RPCS="${RPC_ENDPOINT:-https://api.mainnet-beta.solana.com}"
RELAYS="${JITO_RELAYS:-https://ny.mainnet.block-engine.jito.wtf,https://va.mainnet.block-engine.jito.wtf}"
for u in ${RPCS//,/ }; do h=$(echo "$u" | sed -E 's#https?://([^/]+)/?.*#\1#'); echo "-- $h"; ping -c 3 -W 1 "$h" || true; done
for u in ${RELAYS//,/ }; do h=$(echo "$u" | sed -E 's#https?://([^/]+)/?.*#\1#'); echo "-- $h"; ping -c 3 -W 1 "$h" || true; done

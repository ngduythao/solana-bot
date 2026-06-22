#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
IFACES=${IFACES:-"ens3,eth0"}
MTU=${MTU:-9000}
if [ "$(id -u)" -ne 0 ]; then
  echo "[!] setup_mtu.sh should run as root (sudo)"; exit 0
fi
IFS=',' read -ra ARR <<< "$IFACES"
for i in "${ARR[@]}"; do
  [ -z "$i" ] && continue
  echo "[*] Setting MTU $MTU on $i"
  ip link set dev "$i" mtu "$MTU" || true
done
echo "[*] Current MTUs:"
ip -br link | awk '{print $1, $3}'

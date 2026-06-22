#!/usr/bin/env bash
set -euo pipefail
echo "== UFW status =="
ufw status || true
echo "== Listening ports =="
ss -ltnp | awk 'NR==1 || /:22 |:8080 |:8081 |:6379 /'
echo "== IP/route =="
ip -4 addr show | awk '/inet /{print $2,$NF}'
ip route get 1.1.1.1 2>/dev/null || true

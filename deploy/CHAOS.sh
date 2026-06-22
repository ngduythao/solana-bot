
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  kill-executor)
    pkill -f jupiter_executor.py || true
    ;;
  flap-net)
    sudo tc qdisc add dev ${IFACE:-eth0} root netem loss 5% delay 50ms || true
    sleep 5
    sudo tc qdisc del dev ${IFACE:-eth0} root || true
    ;;
  fill-disk)
    fallocate -l 512M /tmp/chaos_fill.img && sleep 5 && rm -f /tmp/chaos_fill.img
    ;;
  *)
    echo "Usage: $0 {kill-executor|flap-net|fill-disk}"
    ;;
esac

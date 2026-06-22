
#!/usr/bin/env bash
echo "[CHAOS] Flapping network for 10s"
sudo ip link set eth0 down; sleep 10; sudo ip link set eth0 up

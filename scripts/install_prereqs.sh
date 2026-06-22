#!/usr/bin/env bash
set -euo pipefail
sudo apt update
sudo apt -y install python3 python3-venv python3-pip redis-server tmux unzip curl jq gnupg net-tools iproute2 ca-certificates ufw chrony
sudo systemctl enable --now redis-server chrony || true

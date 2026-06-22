#!/usr/bin/env bash
set -euo pipefail

echo "[*] Fixing Docker install on Ubuntu 24.04 (containerd conflicts)..."

sudo systemctl stop docker 2>/dev/null || true
sudo systemctl stop containerd 2>/dev/null || true

sudo apt-get remove -y docker.io docker-doc docker-compose podman-docker containerd containerd.io runc || true
sudo apt-get -y autoremove || true
sudo apt-get -y autoclean || true
sudo apt-get -y clean || true
sudo dpkg --configure -a || true
sudo apt-get -f install -y || true

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable --now docker

echo "[OK] Docker installed."
docker --version || true
docker compose version || true

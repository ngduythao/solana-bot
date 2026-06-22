#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update -y
sudo apt-get install -y git curl build-essential pkg-config libssl-dev python3 python3-venv python3-pip         redis-server gpg tmux

sudo systemctl enable redis-server
sudo systemctl start redis-server

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
for req in $(find . -maxdepth 3 -name requirements.txt); do
  echo "[+] Installing requirements in $req"
  pip install -r "$req" || true
done
echo "[+] Copy .env.example to .env and edit values"
[ -f .env ] || cp .env.example .env
echo "[+] Done. Next: ./scripts/run_all.sh"

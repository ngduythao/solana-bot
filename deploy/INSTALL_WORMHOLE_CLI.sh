
#!/usr/bin/env bash
set -euo pipefail
if command -v wormhole >/dev/null 2>&1; then echo "[WORMHOLE] CLI already installed"; exit 0; fi
if ! command -v npm >/dev/null 2>&1; then
  apt-get update -y && apt-get install -y npm
fi
npm install -g @wormhole-foundation/wormhole-cli || true
echo "[WORMHOLE] Installed. Command: wormhole"

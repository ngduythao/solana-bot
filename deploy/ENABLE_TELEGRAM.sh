
#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$BASE_DIR/solana-bot/.venv/bin/activate"
pip install -r "$BASE_DIR/solana-bot/deploy/requirements_telegram.txt"
echo "[TELEGRAM] Python deps installed."

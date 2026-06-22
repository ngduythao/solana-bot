
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
OUT="/var/backups/solbot"
sudo mkdir -p "$OUT"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
pushd "$BASE_DIR" >/dev/null
sudo redis-cli save || true
sudo tar -czf "$OUT/snapshot-$TS.tgz"   /etc/solbot/.env   solana-bot/adapters/programs.yaml   solana-bot/adapters/market_registry.yaml   /var/log/solbot || true
popd >/dev/null
echo "[SNAPSHOT] saved to $OUT/snapshot-$TS.tgz"

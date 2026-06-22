
#!/usr/bin/env bash
set -euo pipefail
DEST="/var/backups/solbot"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="$DEST/snap-$TS.tar.gz"
mkdir -p "$DEST"
echo "[SNAP] Exporting state -> $OUT"
tar -czf "$OUT"   /etc/solbot/.env   /etc/solbot/SEAL.json 2>/dev/null || true
# redis dump (if rdb/aof exist)
[ -f /var/lib/redis/dump.rdb ] && cp /var/lib/redis/dump.rdb "$DEST/dump-$TS.rdb" || true
[ -f /var/lib/redis/appendonly.aof ] && cp /var/lib/redis/appendonly.aof "$DEST/aof-$TS.aof" || true
echo "[SNAP] Done."

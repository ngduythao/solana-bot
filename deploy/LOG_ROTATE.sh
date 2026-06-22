
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
DST="/var/log/solbot"
sudo mkdir -p "$DST"
for f in /tmp/*.log; do
  [ -f "$f" ] || continue
  sudo gzip -c "$f" > "$DST/$(basename "$f").$TS.gz" || true
  : > "$f" || true
done
echo "[ROTATE] done at $TS -> $DST"

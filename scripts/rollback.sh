#!/usr/bin/env bash
set -euo pipefail
if [[ $(id -u) -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/rollback.sh [index]"
  exit 1
fi
REL_DIR="/opt/solbot_releases"
CUR_LINK="/opt/solbot_current"
cd "$REL_DIR"
LIST=$(ls -1dt solbot-*)
echo "Available releases:"
nl -w2 -s': ' <<< "$LIST"
IDX="${1:-2}"
TARGET=$(echo "$LIST" | sed -n "${IDX}p")
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "Invalid target"; exit 2
fi
ln -sfn "$REL_DIR/$TARGET" "$CUR_LINK"
systemctl restart solbot.service
echo "Rolled back to $TARGET"

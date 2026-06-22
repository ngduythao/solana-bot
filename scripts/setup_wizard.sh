#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
echo "=== solbot setup wizard (non-dev) ==="
echo "Chọn môi trường:"
echo "  [1] Vultr VPS"
echo "  [2] Vultr Bare Metal (NJ)"
echo "  [3] Vultr Bare Metal (Singapore)"
echo "  [4] Auto (đo RTT tự chọn)"
read -rp "Chọn [1-4]: " CH
case "$CH" in
  1) PRESET="vultr-vps" ;;
  2) PRESET="vultr" ;;
  3) PRESET="vultr-sg" ;;
  4) PRESET="auto" ;;
  *) echo "Invalid"; exit 1 ;;
esac
if [ "$PRESET" != "auto" ]; then cp "configs/.env.preset.$PRESET" .env; else cp "configs/.env.preset.vultr-vps" .env; fi
read -rp "Nhập HELIUS API KEY (Enter bỏ qua): " HELIUS_KEY || true
[ -n "${HELIUS_KEY:-}" ] && sed -i "s|^HELIUS_KEY=.*|HELIUS_KEY=${HELIUS_KEY}|g" .env || true
read -rp "Nhập JITO_BUNDLE_AUTH (Enter bỏ qua): " JITO_KEY || true
[ -n "${JITO_KEY:-}" ] && sed -i "s|^JITO_BUNDLE_AUTH=.*|JITO_BUNDLE_AUTH=${JITO_KEY}|g" .env || true
echo "Mã hoá ví id.json bằng GPG (khuyến nghị)"
read -rp "Đường dẫn id.json (Enter bỏ qua): " KEYFILE || true
if [ -n "${KEYFILE:-}" ] && [ -f "$KEYFILE" ]; then
  sudo mkdir -p /opt/solbot/keys
  if ! gpg --list-keys | grep -q "Solbot Deploy" ; then gpg --quick-generate-key "Solbot Deploy <ops@local>"; fi
  gpg --encrypt --recipient "Solbot Deploy" --output /opt/solbot/keys/id.json.gpg "$KEYFILE"
  shred -u "$KEYFILE" || true
  sudo chmod 600 /opt/solbot/keys/id.json.gpg
  echo "[✓] Đã mã hoá /opt/solbot/keys/id.json.gpg"
fi
if command -v ufw >/dev/null 2>&1; then
  sudo ufw default deny incoming || true
  sudo ufw default allow outgoing || true
  sudo ufw allow 22/tcp || true
  sudo ufw allow 8080/tcp || true
  sudo ufw --force enable || true
fi
./scripts/lint_env.sh || true
echo "[✓] Wizard hoàn tất"
if [ "$PRESET" = "auto" ]; then echo "Chạy: ./scripts/start.sh auto"; else echo "Chạy: ./scripts/start.sh $PRESET"; fi

#!/usr/bin/env bash
set -euo pipefail
echo "🔎 Kiểm tra môi trường..."
command -v docker >/dev/null || { echo "❌ Docker không có"; exit 1; }
command -v docker compose >/dev/null || { echo "❌ Docker Compose không có"; exit 1; }
[ -f wallet/keypair.json ] || echo "⚠️  Thiếu wallet/keypair.json"
[ -f .env ] || echo "⚠️  Thiếu .env (đang dùng .env.example)"
echo "✅ Xong."

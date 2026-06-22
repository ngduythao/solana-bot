#!/usr/bin/env bash
set -euo pipefail
docker compose build preselector backrun executor
mkdir -p exports
docker save solbotpro-preselector:local | gzip > exports/preselector.tar.gz
docker save solbotpro-backrun:local | gzip > exports/backrun.tar.gz
# executor uses rust:1.79-slim base at runtime; image is not custom built, so export compose layer if needed
echo "Đã lưu images vào ./exports/*.tar.gz"

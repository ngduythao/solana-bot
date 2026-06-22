#!/usr/bin/env bash
set -euo pipefail
mkdir -p exports
# x86_64 local tags (if present)
if docker image inspect solbotpro-preselector:local >/dev/null 2>&1; then
  docker save solbotpro-preselector:local | gzip > exports/preselector_amd64.tar.gz
fi
if docker image inspect solbotpro-backrun:local >/dev/null 2>&1; then
  docker save solbotpro-backrun:local | gzip > exports/backrun_amd64.tar.gz
fi
# ARM64 tags (if present)
if docker image inspect solbotpro-preselector:arm64 >/dev/null 2>&1; then
  docker save solbotpro-preselector:arm64 | gzip > exports/preselector_arm64.tar.gz
fi
if docker image inspect solbotpro-backrun:arm64 >/dev/null 2>&1; then
  docker save solbotpro-backrun:arm64 | gzip > exports/backrun_arm64.tar.gz
fi
echo "✅ Exported available images into ./exports/*.tar.gz"

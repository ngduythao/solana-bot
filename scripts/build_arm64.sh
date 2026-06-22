#!/usr/bin/env bash
set -euo pipefail
# Ensure buildx
docker buildx create --name solbotx --use >/dev/null 2>&1 || docker buildx use solbotx
docker buildx inspect --bootstrap
mkdir -p exports

# Build preselector/backrun for linux/arm64
docker buildx build   --platform linux/arm64   -t solbotpro-preselector:arm64 -f docker/Dockerfile.preselector   --load .

docker buildx build   --platform linux/arm64   -t solbotpro-backrun:arm64 -f docker/Dockerfile.backrun   --load .

# Save images
docker save solbotpro-preselector:arm64 | gzip > exports/preselector_arm64.tar.gz
docker save solbotpro-backrun:arm64 | gzip > exports/backrun_arm64.tar.gz

echo "✅ Built and saved ARM64 images to exports/*.tar.gz"
echo "➡️  On target Mac M-series, load with:"
echo "    docker load -i exports/preselector_arm64.tar.gz"
echo "    docker load -i exports/backrun_arm64.tar.gz"

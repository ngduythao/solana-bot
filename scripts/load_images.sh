#!/usr/bin/env bash
set -euo pipefail
for f in exports/*tar.gz; do
  echo "Loading $f"
  gunzip -c "$f" | docker load
done
echo "✅ Loaded all images from exports/"

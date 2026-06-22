#!/usr/bin/env bash
set -euo pipefail
NAME=solbot9_project_$(date +%Y%m%d_%H%M%S).tar.gz
tar -czf $NAME .
mkdir -p exports
mv $NAME exports/
echo "✅ Packed repo to exports/$NAME"

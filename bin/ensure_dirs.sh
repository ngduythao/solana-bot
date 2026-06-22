#!/usr/bin/env bash
set -euo pipefail
mkdir -p dashboard tuner analytics certs prometheus grafana secrets orchestrator guard metrics_exporter
touch config.yaml
echo "[OK] Ensured host directories exist."

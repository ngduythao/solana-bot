#!/usr/bin/env bash
set -euo pipefail
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"
echo "✅ Created certs/cert.pem and certs/key.pem"
